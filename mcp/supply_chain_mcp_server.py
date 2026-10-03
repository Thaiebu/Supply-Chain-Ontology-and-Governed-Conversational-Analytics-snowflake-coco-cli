#!/usr/bin/env python3
"""
supply_chain_mcp_server.py
MCP server exposing supply chain OTD breach detection tools.
Runs as a stdio transport server for CoCo CLI integration.

Tools:
  - check_otd_breach: Check if a supplier is breaching their SLA OTD target
  - sla_compliance_report: Get full SLA compliance summary across all suppliers

Usage:
  Registered in ~/.snowflake/cortex/mcp.json for CoCo CLI.
  CoCo invokes tools via: "Check OTD breach for SUP-009"
"""

import json
import os
import sys

import snowflake.connector
import toml
from mcp.server.mcpserver import MCPServer

mcp = MCPServer(
    "supply-chain-alerts",
    instructions=(
        "Supply chain OTD monitoring tools. Use check_otd_breach to check "
        "if a specific supplier is breaching their contracted SLA delivery target. "
        "Use sla_compliance_report to get a full compliance overview."
    ),
)


def _get_snowflake_connection():
    """Create a Snowflake connection from ~/.snowflake/connections.toml."""
    config_path = os.path.expanduser("~/.snowflake/connections.toml")
    config = toml.load(config_path)
    conn_name = os.environ.get("SNOWFLAKE_DEFAULT_CONNECTION_NAME", "WZ37797")
    params = config.get(conn_name, config.get("default", {}))

    return snowflake.connector.connect(
        account=params.get("account", params.get("accountname", "")),
        user=params.get("user", params.get("username", "")),
        password=params.get("password", ""),
        warehouse=params.get("warehouse", "COMPUTE_WH"),
        database="SUPPLY_CHAIN_DB",
        schema="ANALYTICS",
        role=params.get("role", "ACCOUNTADMIN"),
        authenticator=params.get("authenticator", "snowflake"),
    )


@mcp.tool()
def check_otd_breach(supplier_id: str) -> str:
    """Check if a supplier is breaching their contracted SLA OTD target.

    Returns an alert payload with SLA target, actual OTD, gap, and status.
    Use this when someone asks about a specific supplier's delivery compliance.

    Args:
        supplier_id: The supplier ID to check (e.g. SUP-001, SUP-009).
    """
    supplier_id = supplier_id.strip().upper()

    try:
        conn = _get_snowflake_connection()
        cur = conn.cursor(snowflake.connector.DictCursor)
        cur.execute(
            """
            SELECT *
            FROM SUPPLY_CHAIN_DB.ANALYTICS.V_SLA_VS_ACTUAL_OTD
            WHERE supplier_id = %s
            """,
            (supplier_id,),
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            return json.dumps(
                {
                    "status": "NOT_FOUND",
                    "message": f"No SLA record found for supplier {supplier_id}.",
                    "available_suppliers": "Query V_SLA_VS_ACTUAL_OTD for the full list.",
                },
                indent=2,
            )

        alert = {
            "supplier_id": row["SUPPLIER_ID"],
            "supplier_name": row["SUPPLIER_NAME"],
            "country": row["COUNTRY"],
            "sla_target_pct": float(row["SLA_TARGET_PCT"]),
            "actual_otd_pct": float(row["ACTUAL_OTD_PCT"]),
            "gap_pct": float(row["GAP_PCT"]),
            "total_closed_pos": int(row["TOTAL_CLOSED_POS"]),
            "sla_status": row["SLA_STATUS"],
            "penalty_clause": row["PENALTY_CLAUSE"],
        }

        if alert["sla_status"] == "BREACH":
            alert["alert_level"] = "CRITICAL"
            alert["recommendation"] = (
                f"{alert['supplier_name']} is {abs(alert['gap_pct']):.1f} points below "
                f"their {alert['sla_target_pct']:.0f}% SLA target. "
                f"Escalation Level 2 triggered: Corrective Action Plan required within 30 days. "
                f"Penalty applies: {alert['penalty_clause']}."
            )
        elif alert["sla_status"] == "WARNING":
            alert["alert_level"] = "WARNING"
            alert["recommendation"] = (
                f"{alert['supplier_name']} is within 3 points of their SLA target. "
                f"Escalation Level 1: Written notice recommended."
            )
        else:
            alert["alert_level"] = "OK"
            alert["recommendation"] = (
                f"{alert['supplier_name']} is meeting their SLA commitment "
                f"({alert['actual_otd_pct']:.1f}% vs {alert['sla_target_pct']:.0f}% target)."
            )

        return json.dumps(alert, indent=2)

    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)}, indent=2)


@mcp.tool()
def sla_compliance_report() -> str:
    """Get the full SLA compliance report for all contracted suppliers.

    Returns a summary with breach/warning/meeting counts and the top breaching suppliers.
    Use this for executive-level supply chain health checks.
    """
    try:
        conn = _get_snowflake_connection()
        cur = conn.cursor(snowflake.connector.DictCursor)
        cur.execute(
            "SELECT * FROM SUPPLY_CHAIN_DB.ANALYTICS.V_SLA_VS_ACTUAL_OTD"
        )
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return json.dumps({"status": "NO_DATA", "message": "No SLA data found."})

        breach = [r for r in rows if r["SLA_STATUS"] == "BREACH"]
        warning = [r for r in rows if r["SLA_STATUS"] == "WARNING"]
        meeting = [r for r in rows if r["SLA_STATUS"] == "MEETING SLA"]

        report = {
            "report_title": "Supplier SLA Compliance Report",
            "total_suppliers": len(rows),
            "summary": {
                "breach": len(breach),
                "warning": len(warning),
                "meeting_sla": len(meeting),
            },
            "top_breaches": [
                {
                    "supplier": r["SUPPLIER_NAME"],
                    "country": r["COUNTRY"],
                    "sla_target": float(r["SLA_TARGET_PCT"]),
                    "actual_otd": float(r["ACTUAL_OTD_PCT"]),
                    "gap": float(r["GAP_PCT"]),
                }
                for r in sorted(breach, key=lambda x: float(x["GAP_PCT"]))[:5]
            ],
            "top_performers": [
                {
                    "supplier": r["SUPPLIER_NAME"],
                    "country": r["COUNTRY"],
                    "sla_target": float(r["SLA_TARGET_PCT"]),
                    "actual_otd": float(r["ACTUAL_OTD_PCT"]),
                    "gap": float(r["GAP_PCT"]),
                }
                for r in sorted(meeting, key=lambda x: float(x["GAP_PCT"]), reverse=True)[:3]
            ],
        }

        return json.dumps(report, indent=2)

    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)}, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
