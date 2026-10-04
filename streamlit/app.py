"""
Supply Chain Intelligence Portal
Streamlit app demonstrating governed (Cortex Analyst) vs ungoverned (raw SQL) analytics.
"""

import json
import os
import streamlit as st

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
_CONN_NAME = os.getenv("SNOWFLAKE_DEFAULT_CONNECTION_NAME") or "default"
_MODEL_PATH = "@SUPPLY_CHAIN_DB.ANALYTICS.SEMANTIC_MODELS_STAGE/supply_chain_ontology.yaml"

def get_session():
    return st.connection("snowflake").session()

# ---------------------------------------------------------------------------
# Metric Catalog
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Metric Contract: ONE definition, MULTIPLE governed lenses
# ---------------------------------------------------------------------------
# The ontology's key insight: a canonical metric has ONE business definition
# but resolves through different lenses depending on business context.
# The definition is governed; the lens determines which data applies.
METRIC_CONTRACTS = {
    "on_time_delivery": {
        "name": "On-Time Delivery (OTD)",
        "business_definition": (
            "Percentage of eligible deliveries completed on or before "
            "the applicable committed date."
        ),
        "numerator": "Deliveries where actual_date <= committed_date",
        "denominator": "All eligible (closed/completed) deliveries",
        "exclusions": ["Cancelled orders", "Open/pending orders"],
        "lenses": {
            "Supplier (Procurement)": {
                "committed_date": "promised_date (PO)",
                "actual_date": "receipt_date",
                "table": "FCT_PURCHASE_ORDERS",
            },
            "Carrier (Logistics)": {
                "committed_date": "estimated_delivery_date",
                "actual_date": "actual_delivery_date",
                "table": "FCT_SHIPMENTS",
            },
            "Customer (Planning/OTIF)": {
                "committed_date": "request_date + 5-day SLA grace",
                "actual_date": "shipped_date",
                "table": "FCT_CUSTOMER_ORDERS",
                "extra": "+ shipped_qty >= ordered_qty (In-Full)",
            },
            "Enterprise (Executive)": {
                "committed_date": "All three above",
                "actual_date": "Weighted average across all channels",
                "table": "All 3 fact tables (CTE blend)",
            },
        },
    },
}

METRIC_CATALOG = {
    "On-Time Delivery (OTD)": {
        "definition": "Percentage of deliveries completed on or before the committed date.",
        "lenses": {
            "Procurement (Supplier OTD)": "COUNT(receipt_date <= promised_date) / COUNT(*) on FCT_PURCHASE_ORDERS",
            "Logistics (Carrier OTD)": "COUNT(actual_delivery_date <= estimated_delivery_date) / COUNT(*) on FCT_SHIPMENTS",
            "Planning (Customer OTIF)": "COUNT(shipped_date <= request_date+5 AND shipped_qty >= ordered_qty) / COUNT(*) on FCT_CUSTOMER_ORDERS",
            "Enterprise OTD": "Weighted average across all three lenses",
        },
    },
    "Fill Rate": {
        "definition": "Percentage of ordered quantity that was actually received or shipped.",
        "formula": "SUM(received_qty) / SUM(order_qty)",
        "source": "FCT_PURCHASE_ORDERS (inbound) or FCT_CUSTOMER_ORDERS (outbound)",
    },
    "Days of Inventory (DOI)": {
        "definition": "Estimated number of days current stock will last at current demand rate.",
        "formula": "(Total Received - Total Shipped) / (Annual Demand / 365)",
        "source": "FCT_PURCHASE_ORDERS + FCT_CUSTOMER_ORDERS",
    },
    "Landed Cost": {
        "definition": "Fully loaded cost per unit including unit price, freight, and customs/tariff.",
        "formula": "AVG(unit_cost_ea + freight_cost/order_qty + customs_tariff_cost/order_qty)",
        "source": "FCT_PURCHASE_ORDERS",
    },
}

# ---------------------------------------------------------------------------
# Persona configuration
# ---------------------------------------------------------------------------
PERSONAS = {
    "VP Executive": {
        "icon": "👔",
        "default_question": "What is our canonical enterprise OTD rate across all channels?",
        "focus": "Enterprise-wide KPIs and cross-functional performance",
    },
    "Procurement Manager": {
        "icon": "📦",
        "default_question": "What is our inbound supplier on-time delivery rate?",
        "focus": "Supplier performance, landed costs, and PO fill rates",
    },
    "Logistics Director": {
        "icon": "🚚",
        "default_question": "Which carrier has the best on-time delivery rate?",
        "focus": "Carrier transit times, shipment delays, and route optimization",
    },
    "Supply Chain Planner": {
        "icon": "📊",
        "default_question": "What is the customer OTIF rate by customer tier?",
        "focus": "Customer fulfillment, inventory levels, and demand planning",
    },
}

# ---------------------------------------------------------------------------
# Governed: Cortex Analyst via REST
# ---------------------------------------------------------------------------
def _get_rest_params(session):
    """Extract host and token from the Snowpark session's underlying connector."""
    # Try multiple paths to find the REST token
    conn = session._conn

    # Path 1: Snowpark session -> _conn -> _rest
    if hasattr(conn, '_rest') and hasattr(conn._rest, '_token'):
        return conn._rest._host, conn._rest._token

    # Path 2: Snowpark session -> _conn -> _cursor -> connection
    if hasattr(conn, '_cursor'):
        raw = conn._cursor.connection
        if hasattr(raw, 'rest') and hasattr(raw.rest, 'token'):
            return raw.rest._host, raw.rest.token

    # Path 3: via _sf_connection
    if hasattr(conn, '_sf_connection'):
        sf = conn._sf_connection
        if hasattr(sf, 'rest'):
            return sf.rest._host, sf.rest.token

    # Path 4: via the Streamlit connection's raw connector
    try:
        st_conn = st.connection("snowflake")
        raw_conn = st_conn._instance
        if hasattr(raw_conn, 'rest'):
            return raw_conn.rest._host, raw_conn.rest.token
        if hasattr(raw_conn, '_rest'):
            return raw_conn._rest._host, raw_conn._rest._token
    except Exception:
        pass

    raise RuntimeError("Could not extract REST token from session")


def query_cortex_analyst(session, question: str) -> dict:
    """Query Cortex Analyst using the semantic model on stage."""
    import requests

    host, token = _get_rest_params(session)

    url = f"https://{host}/api/v2/cortex/analyst/message"
    headers = {
        "Authorization": f'Snowflake Token="{token}"',
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": question}]}
        ],
        "semantic_model_file": _MODEL_PATH,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def run_governed_query(session, question: str):
    """Run a governed query through Cortex Analyst, with semantic-aware fallback."""
    analyst_error = None

    # Attempt 1: Cortex Analyst REST API
    try:
        response = query_cortex_analyst(session, question)
        sql_stmt = None
        text_resp = None

        for content in response.get("message", {}).get("content", []):
            if content.get("type") == "sql":
                sql_stmt = content.get("statement", "")
            elif content.get("type") == "text":
                text_resp = content.get("text", "")

        result_df = None
        if sql_stmt:
            result_df = session.sql(sql_stmt).to_pandas()

        return {
            "mode": "GOVERNED",
            "sql": sql_stmt,
            "text": text_resp,
            "data": result_df,
            "source": "Cortex Analyst + Semantic Model",
            "lineage": _MODEL_PATH,
        }
    except Exception as e:
        analyst_error = str(e)

    # Attempt 2: Semantic-aware fallback using CORTEX.COMPLETE with metric definitions
    try:
        semantic_prompt = """You are a governed supply chain analytics SQL generator.
You MUST use these EXACT metric definitions from the semantic model:

SUPPLIER OTD = ROUND(100.0 * SUM(CASE WHEN receipt_date <= promised_date THEN 1 ELSE 0 END) / NULLIF(COUNT(CASE WHEN receipt_date IS NOT NULL THEN 1 END), 0), 2)
  Source: SUPPLY_CHAIN_DB.ANALYTICS.FCT_PURCHASE_ORDERS

CARRIER OTD = ROUND(100.0 * SUM(CASE WHEN actual_delivery_date <= estimated_delivery_date THEN 1 ELSE 0 END) / NULLIF(COUNT(CASE WHEN actual_delivery_date IS NOT NULL THEN 1 END), 0), 2)
  Source: SUPPLY_CHAIN_DB.ANALYTICS.FCT_SHIPMENTS

CUSTOMER OTIF = ROUND(100.0 * SUM(CASE WHEN shipped_date <= DATEADD('day', 5, request_date) AND shipped_qty >= ordered_qty THEN 1 ELSE 0 END) / NULLIF(COUNT(CASE WHEN shipped_date IS NOT NULL THEN 1 END), 0), 2)
  Source: SUPPLY_CHAIN_DB.ANALYTICS.FCT_CUSTOMER_ORDERS

FILL RATE = ROUND(100.0 * SUM(received_qty) / NULLIF(SUM(order_qty), 0), 2)
  Source: SUPPLY_CHAIN_DB.ANALYTICS.FCT_PURCHASE_ORDERS

LANDED COST = ROUND(AVG(unit_cost_ea + (freight_cost / NULLIF(order_qty, 0)) + (customs_tariff_cost / NULLIF(order_qty, 0))), 2)
  Source: SUPPLY_CHAIN_DB.ANALYTICS.FCT_PURCHASE_ORDERS

Tables: SUPPLY_CHAIN_DB.ANALYTICS.FCT_PURCHASE_ORDERS, FCT_SHIPMENTS, FCT_CUSTOMER_ORDERS, DIM_SUPPLIER, DIM_PLANT, DIM_CUSTOMER, DIM_PART
Always use fully qualified table names. Return ONLY the SQL query."""

        escaped_q = question.replace("'", "''")
        escaped_prompt = semantic_prompt.replace("'", "''")

        sql_call = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'llama3.1-70b',
            '{escaped_prompt}\n\nQuestion: {escaped_q}'
        ) AS response
        """
        raw = session.sql(sql_call).collect()
        raw_response = raw[0]["RESPONSE"] if raw else ""

        sql_stmt = raw_response.strip()
        if "```sql" in sql_stmt:
            sql_stmt = sql_stmt.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql_stmt:
            sql_stmt = sql_stmt.split("```")[1].split("```")[0].strip()

        result_df = session.sql(sql_stmt).to_pandas()

        return {
            "mode": "GOVERNED",
            "sql": sql_stmt,
            "text": f"(Semantic-aware fallback; Analyst API unavailable: {analyst_error})",
            "data": result_df,
            "source": "Cortex Complete + Semantic Metric Definitions (fallback)",
            "lineage": _MODEL_PATH,
        }
    except Exception as e2:
        return {
            "mode": "GOVERNED",
            "sql": None,
            "text": f"Cortex Analyst error: {analyst_error}\nFallback error: {str(e2)}",
            "data": None,
            "source": "Error - see details",
            "lineage": _MODEL_PATH,
        }


# ---------------------------------------------------------------------------
# Ungoverned: Raw text-to-SQL (no semantic layer)
# ---------------------------------------------------------------------------
UNGOVERNED_PROMPT = """You are a SQL assistant. Generate a Snowflake SQL query to answer the question.
Available tables (all in SUPPLY_CHAIN_DB.ANALYTICS):
- FCT_PURCHASE_ORDERS (po_id, part_id, supplier_id, plant_id, order_qty, received_qty, unit_cost_ea, freight_cost, customs_tariff_cost, promised_date, receipt_date, po_status)
- FCT_SHIPMENTS (ship_id, po_id, carrier_name, origin_plant_id, dest_plant_id, ship_date, estimated_delivery_date, actual_delivery_date, transit_status)
- FCT_CUSTOMER_ORDERS (order_id, customer_id, part_id, plant_id, ordered_qty, shipped_qty, request_date, shipped_date, delivery_status)
- DIM_SUPPLIER (supplier_id, supplier_name, country, lead_time_days, rating)
- DIM_PLANT (plant_id, plant_name, city, country, capacity_units)
- DIM_CUSTOMER (customer_id, customer_name, industry, country, tier)
- DIM_PART (part_id, part_name, category, unit_cost, supplier_id, plant_id)

Return ONLY the SQL query, no explanation. Do NOT use fully qualified names."""


def run_ungoverned_query(session, question: str):
    """Run an ungoverned text-to-SQL query without the semantic layer."""
    try:
        prompt = f"{UNGOVERNED_PROMPT}\n\nQuestion: {question}"
        sql_call = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'llama3.1-70b',
            '{prompt.replace("'", "''")}'
        ) AS response
        """
        raw = session.sql(sql_call).collect()
        raw_response = raw[0]["RESPONSE"] if raw else ""

        # Extract SQL from response
        sql_stmt = raw_response.strip()
        if "```sql" in sql_stmt:
            sql_stmt = sql_stmt.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql_stmt:
            sql_stmt = sql_stmt.split("```")[1].split("```")[0].strip()

        # Fix table references to be fully qualified
        for tbl in [
            "FCT_PURCHASE_ORDERS", "FCT_SHIPMENTS", "FCT_CUSTOMER_ORDERS",
            "DIM_SUPPLIER", "DIM_PLANT", "DIM_CUSTOMER", "DIM_PART",
        ]:
            sql_stmt = sql_stmt.replace(
                f" {tbl}", f" SUPPLY_CHAIN_DB.ANALYTICS.{tbl}"
            ).replace(
                f"\n{tbl}", f"\nSUPPLY_CHAIN_DB.ANALYTICS.{tbl}"
            )

        result_df = None
        exec_error = None
        try:
            result_df = session.sql(sql_stmt).to_pandas()
        except Exception as ex:
            exec_error = str(ex)

        return {
            "mode": "UNGOVERNED",
            "sql": sql_stmt,
            "text": raw_response if exec_error else None,
            "data": result_df,
            "source": "Raw LLM Text-to-SQL (no semantic layer)",
            "lineage": "None - direct table access",
            "warning": exec_error,
        }
    except Exception as e:
        return {
            "mode": "UNGOVERNED",
            "sql": None,
            "text": f"Error: {str(e)}",
            "data": None,
            "source": "Error",
            "lineage": "None",
        }


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def render_sidebar():
    """Render the metric contract, catalog, and persona info in the sidebar."""
    with st.sidebar:
        # --- Metric Contract (the key differentiator) ---
        st.header("Metric Contract")
        st.caption(
            "ONE canonical definition per metric. "
            "The business context determines the lens."
        )
        for contract in METRIC_CONTRACTS.values():
            with st.expander(contract["name"], expanded=True):
                st.markdown(f"**Definition:** {contract['business_definition']}")
                st.markdown(f"**Numerator:** {contract['numerator']}")
                st.markdown(f"**Denominator:** {contract['denominator']}")
                st.markdown("**Governed Lenses:**")
                for lens_name, lens_def in contract["lenses"].items():
                    committed = lens_def["committed_date"]
                    actual = lens_def["actual_date"]
                    table = lens_def["table"]
                    extra = lens_def.get("extra", "")
                    st.markdown(
                        f"- **{lens_name}:** `{actual} <= {committed}` "
                        f"{extra} ({table})"
                    )
                st.info(
                    "Same definition. Different context. "
                    "The numbers differ because the committed dates differ "
                    "-- not because the metric is inconsistent."
                )

        st.divider()

        # --- Metric Catalog ---
        st.header("Metric Catalog")
        st.caption("Canonical metric definitions for the supply chain domain")

        for metric_name, details in METRIC_CATALOG.items():
            with st.expander(metric_name, expanded=False):
                st.markdown(f"**Definition:** {details['definition']}")
                if "formula" in details:
                    st.code(details["formula"], language="sql")
                if "source" in details:
                    st.markdown(f"**Source:** `{details['source']}`")
                if "lenses" in details:
                    st.markdown("**Lenses:**")
                    for lens, formula in details["lenses"].items():
                        st.markdown(f"- **{lens}:** `{formula}`")

        st.divider()
        st.markdown("**Semantic Model**")
        st.code(_MODEL_PATH, language="text")
        st.markdown("**Database:** `SUPPLY_CHAIN_DB`")
        st.markdown("**Schema:** `ANALYTICS`")


def render_result(result: dict, persona: str):
    """Render the query result with transparency panel."""
    mode = result["mode"]

    # Status badge
    if mode == "GOVERNED":
        st.success(f"GOVERNED MODE | Source: {result['source']}")
    else:
        st.warning(f"UNGOVERNED MODE | Source: {result['source']}")

    if result.get("warning"):
        st.error(f"Execution error: {result['warning']}")

    # Text response
    if result.get("text"):
        st.markdown(result["text"])

    # Data display
    if result.get("data") is not None and not result["data"].empty:
        df = result["data"]
        if len(df) == 1 and len(df.columns) == 1:
            val = df.iloc[0, 0]
            col_name = df.columns[0]
            st.metric(label=col_name, value=f"{val}")
        elif len(df) <= 3 and len(df.columns) == 1:
            for _, row in df.iterrows():
                st.metric(label=df.columns[0], value=f"{row.iloc[0]}")
        else:
            st.dataframe(df, use_container_width=True)
    elif result.get("data") is not None and result["data"].empty:
        st.info("ℹ️ Query executed successfully, but returned 0 records matching this criteria.")

    # SQL & Formula Transparency Panel
    with st.expander("SQL & Formula Transparency", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Mode:**")
            st.markdown(f"`{mode}`")
            st.markdown("**Data Lineage:**")
            st.markdown(f"`{result.get('lineage', 'N/A')}`")
        with col2:
            st.markdown("**Source:**")
            st.markdown(f"`{result.get('source', 'N/A')}`")
            st.markdown("**Persona:**")
            st.markdown(f"`{persona}`")

        if result.get("sql"):
            st.markdown("**Generated SQL:**")
            st.code(result["sql"], language="sql")
        else:
            st.info("No SQL was generated for this query.")

        if mode == "GOVERNED":
            st.markdown("**Governance Chain:**")
            st.markdown(
                "1. Natural language question\n"
                "2. Cortex Analyst parses against semantic model\n"
                "3. Verified queries matched (if applicable)\n"
                "4. SQL generated from metric definitions\n"
                "5. Results returned with full lineage"
            )
        else:
            st.markdown("**Risk Factors (Ungoverned):**")
            st.markdown(
                "- No metric definitions enforced\n"
                "- No verified query matching\n"
                "- Potential for hallucinated joins or wrong aggregations\n"
                "- No lineage or audit trail\n"
                "- Same question may produce different SQL each time"
            )


def main():
    st.set_page_config(
        page_title="Supply Chain Intelligence Portal",
        page_icon="🏭",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Supply Chain Intelligence Portal")
    st.caption("Governed analytics powered by Cortex Analyst + Semantic Model")

    render_sidebar()

    # --- Controls row ---
    col_persona, col_mode, col_spacer = st.columns([2, 2, 3])

    with col_persona:
        persona = st.selectbox(
            "Select Persona",
            list(PERSONAS.keys()),
            format_func=lambda x: f"{PERSONAS[x]['icon']} {x}",
        )

    with col_mode:
        governed = st.toggle("Governed Mode", value=True)
        if governed:
            st.caption("Using Cortex Analyst + Semantic Model")
        else:
            st.caption("Using raw Text-to-SQL (no semantic layer)")

    # Persona context
    persona_info = PERSONAS[persona]
    st.info(f"**{persona_info['icon']} {persona}** | Focus: {persona_info['focus']}")

    # --- Question input ---
    if "question" not in st.session_state:
        st.session_state["question"] = persona_info["default_question"]

    question = st.text_input(
        "Ask a supply chain question:",
        value=st.session_state["question"],
        key="question_input",
        placeholder="e.g., What is our supplier OTD rate by country?",
    )
    st.session_state["question"] = question

    # --- Quick question buttons ---
    st.markdown("**Quick questions:**")
    quick_cols = st.columns(4)
    quick_questions = [
        "What is the overall fill rate?",
        "What is the average landed cost by supplier?",
        "Show monthly PO trend with late delivery count.",
        "Which suppliers have the most late deliveries?",
    ]
    for i, qq in enumerate(quick_questions):
        if quick_cols[i].button(qq, key=f"quick_{i}", use_container_width=True):
            st.session_state["question"] = qq
            st.rerun()

    # --- Ambiguity guardrail for OTD questions ---
    _q_lower = question.lower()
    _otd_keywords = ["otd", "on-time delivery", "on time delivery", "delivery rate", "delivery performance"]
    _lens_keywords = ["supplier", "carrier", "customer", "enterprise", "procurement", "logistics", "planning", "otif", "inbound", "outbound", "transit"]
    _is_ambiguous_otd = (
        any(k in _q_lower for k in _otd_keywords)
        and not any(k in _q_lower for k in _lens_keywords)
        and governed
    )

    if _is_ambiguous_otd:
        st.warning(
            "**Ambiguous metric detected.** Your question mentions OTD without "
            "specifying a business lens. The ontology defines 4 governed OTD lenses:"
        )
        _disambig_cols = st.columns(4)
        _lens_labels = [
            ("Supplier OTD", "Inbound PO delivery", "receipt_date <= promised_date"),
            ("Carrier OTD", "Shipment transit SLA", "actual_delivery <= estimated_delivery"),
            ("Customer OTIF", "Order fulfillment", "shipped_date <= request_date + qty check"),
            ("Enterprise OTD", "Weighted blend (default)", "All 3 channels combined"),
        ]
        for col, (name, desc, formula) in zip(_disambig_cols, _lens_labels):
            col.markdown(f"**{name}**")
            col.caption(desc)
            col.code(formula, language="text")

        st.info(
            "For an executive-level question, the governed default is **Enterprise OTD**. "
            "To get a specific lens, rephrase your question (e.g., 'What is our **supplier** OTD?')."
        )

    # --- Execute ---
    if st.button("Run Query", type="primary", use_container_width=True):
        session = get_session()

        with st.spinner(
            "Querying via Cortex Analyst..." if governed else "Generating raw SQL..."
        ):
            if governed:
                result = run_governed_query(session, question)
            else:
                result = run_ungoverned_query(session, question)

        render_result(result, persona)

        # Side-by-side comparison hint
        if not governed:
            st.divider()
            st.markdown(
                "**Toggle Governed Mode** to see how the same question "
                "resolves through the semantic layer with metric definitions, "
                "verified queries, and full SQL lineage."
            )

    # --- Comparison mode ---
    with st.expander("Side-by-Side Comparison (Governed vs Ungoverned)", expanded=False):
        st.markdown(
            "Run the same question in both modes to see the difference "
            "in SQL generation, metric resolution, and result consistency."
        )
        if st.button("Run Comparison", key="compare"):
            session = get_session()

            col_gov, col_ungov = st.columns(2)

            with col_gov:
                st.subheader("Governed")
                with st.spinner("Cortex Analyst..."):
                    gov_result = run_governed_query(session, question)
                render_result(gov_result, persona)

            with col_ungov:
                st.subheader("Ungoverned")
                with st.spinner("Raw LLM..."):
                    ungov_result = run_ungoverned_query(session, question)
                render_result(ungov_result, persona)

    # --- Contract SLA vs Actual OTD ---
    with st.expander("Contract SLA vs Actual OTD (Document Intelligence)", expanded=False):
        st.markdown(
            "Supplier SLA commitments were extracted from an unstructured contract document "
            "using **SNOWFLAKE.CORTEX.COMPLETE()** and compared against actual delivery performance."
        )
        if st.button("Load SLA Compliance Report", key="sla_report"):
            session = get_session()
            with st.spinner("Querying SLA compliance..."):
                try:
                    sla_df = session.sql(
                        "SELECT * FROM SUPPLY_CHAIN_DB.ANALYTICS.V_SLA_VS_ACTUAL_OTD"
                    ).to_pandas()

                    # Summary metrics
                    breach_count = len(sla_df[sla_df["SLA_STATUS"] == "BREACH"])
                    warning_count = len(sla_df[sla_df["SLA_STATUS"] == "WARNING"])
                    meeting_count = len(sla_df[sla_df["SLA_STATUS"] == "MEETING SLA"])

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Breaching SLA", breach_count, delta=None)
                    m2.metric("Warning (within 3pts)", warning_count, delta=None)
                    m3.metric("Meeting SLA", meeting_count, delta=None)

                    # Color-coded table
                    def highlight_status(row):
                        if row["SLA_STATUS"] == "BREACH":
                            return ["background-color: #ffcccc"] * len(row)
                        elif row["SLA_STATUS"] == "WARNING":
                            return ["background-color: #fff3cd"] * len(row)
                        else:
                            return ["background-color: #d4edda"] * len(row)

                    display_cols = [
                        "SUPPLIER_NAME", "COUNTRY", "SLA_TARGET_PCT",
                        "ACTUAL_OTD_PCT", "GAP_PCT", "SLA_STATUS", "TOTAL_CLOSED_POS",
                    ]
                    styled = sla_df[display_cols].style.apply(highlight_status, axis=1)
                    st.dataframe(styled, use_container_width=True)

                    st.caption(
                        "Source: SLA terms extracted from contracts/supplier_sla_agreement.txt "
                        "via SNOWFLAKE.CORTEX.COMPLETE(llama3.1-70b). "
                        "Actual OTD computed from FCT_PURCHASE_ORDERS."
                    )
                except Exception as e:
                    st.error(f"Could not load SLA data: {e}")

    # --- Data Reality / Ground Truth ---
    with st.expander("Synthetic Data Ground Truth", expanded=False):
        st.markdown(
            "This dataset is **intentionally synthetic** with controlled edge cases "
            "to demonstrate that the ontology correctly handles real-world scenarios."
        )

        gt_col1, gt_col2 = st.columns(2)

        with gt_col1:
            st.markdown("**Data Volume**")
            st.markdown(
                "| Entity | Rows |\n"
                "|---|---|\n"
                "| Suppliers | 20 (India, UAE, Germany, USA, China) |\n"
                "| Plants | 5 (Dubai, Abu Dhabi, Mumbai, Chennai, Frankfurt) |\n"
                "| Customers | 25 (Platinum/Gold/Silver tiers) |\n"
                "| Parts | 30 (4 categories) |\n"
                "| Purchase Orders | 500 |\n"
                "| Shipments | 600 (8 carriers) |\n"
                "| Customer Orders | 800 |\n"
                "| **Total** | **1,980 rows** |"
            )

        with gt_col2:
            st.markdown("**Intentional Scenarios**")
            st.markdown(
                "| Scenario | Target Rate | Purpose |\n"
                "|---|---|---|\n"
                "| Late supplier receipts | ~15% | Test Procurement OTD |\n"
                "| Carrier transit delays | ~8% | Test Logistics OTD |\n"
                "| Late customer shipments | ~12% | Test Customer OTD |\n"
                "| Partial order fills | ~5% | Test Fill Rate + OTIF |\n"
                "| SLA breach scenarios | 10 of 20 | Test contract compliance |\n"
                "| Cross-border freight | All 5 countries | Test Landed Cost |"
            )

        st.markdown("---")
        st.markdown("**Why is Customer OTIF so low (~5%)?**")
        st.markdown(
            "This is intentional. Customer OTIF requires **both** on-time delivery "
            "(shipped within 5 days of request) **and** in-full quantity. The synthetic "
            "fulfillment lead time averages ~13.6 days, so most orders exceed the 5-day "
            "SLA window. This demonstrates a critical distinction the ontology governs: "
            "**OTD** (timing only) vs **OTIF** (timing + quantity). An ungoverned LLM "
            "would conflate these two metrics."
        )
        st.markdown(
            "**Why is Carrier OTD ~47%?**  "
            "Ship dates and estimated delivery dates are independently randomized, "
            "creating realistic variance. The ontology correctly separates this from "
            "Supplier OTD (~87%) because they measure different committed dates."
        )


if __name__ == "__main__":
    main()
