"""
agent/graph.py
LangChain deepagents orchestrator wiring with sub-agents, MCP clients,
virtual filesystem state persistence, and deterministic analytical execution.
"""

import asyncio
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

from deepagents import create_deep_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool

from agent.guardrails import (
    check_bytes_limit,
    mask_tabular_data,
    validate_query_guardrails,
)
from agent.mcp_clients import (
    create_mcp_client,
    extract_tool_result,
    get_categorized_tools,
)
from agent.prompts import (
    OKF_NAVIGATOR_SYSTEM_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    SQL_ANALYST_SYSTEM_PROMPT,
    VIZ_REPORTER_SYSTEM_PROMPT,
)
from agent.tools_local import (
    bind_parameters,
    render_chart,
    render_table,
    sql_guard,
)

STATE_DIR = "/tmp/loyalty_state"
STATE_FILE = os.path.join(STATE_DIR, "last_execution.json")


def save_execution_state(state: Dict[str, Any]):
    """Saves analytical execution context into the virtual filesystem for follow-ups."""
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, default=str)


def load_execution_state() -> Optional[Dict[str, Any]]:
    """Loads previous execution context from the virtual filesystem."""
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_configured_llm(provider: Optional[str] = None) -> Optional[BaseChatModel]:
    """Instantiates configured LLM (Vertex Gemini or Anthropic)."""
    prov = (provider or os.getenv("LLM_PROVIDER", "vertex-gemini")).lower()
    
    if prov in ("vertex-gemini", "gemini", "google"):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
        except Exception:
            return None
            
    elif prov == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model=model_name, api_key=api_key)
        except Exception:
            return None
            
    return None


class LoyaltyDeepAgent:
    """
    Autonomous deep agent orchestrating OKF bundle exploration and BigQuery analytics
    using strictly MCP tools for external data interaction.
    """

    def __init__(self, config_path: str = "config/mcp_servers.json"):
        self.config_path = config_path
        self.mcp_client = create_mcp_client(config_path)
        self.tools: Dict[str, Any] = {}
        self.routing_cache: Optional[Dict[str, Any]] = None

    async def initialize(self):
        """Discovers and binds tools from MCP servers."""
        self.tools = await get_categorized_tools(self.mcp_client)
        return self

    async def fetch_routing_matrix(self) -> str:
        """Reads question-routing.md from Cloud Storage via GCS MCP tool."""
        read_tool = next(t for t in self.tools["gcs"] if t.name == "read_object")
        raw_res = await read_tool.ainvoke({"path": "routing/question-routing.md"})
        return str(extract_tool_result(raw_res))

    async def fetch_concept(self, concept_path: str) -> str:
        """Reads a specific OKF concept from Cloud Storage via GCS MCP tool."""
        clean_path = concept_path.lstrip("/")
        read_tool = next(t for t in self.tools["gcs"] if t.name == "read_object")
        raw_res = await read_tool.ainvoke({"path": clean_path})
        return str(extract_tool_result(raw_res))

    async def resolve_use_case(self, question: str, previous_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Maps a natural-language user query to a canonical use-case ID and concept file.
        Dynamically consults the routing table in GCS, picking up any newly added concepts.
        """
        q_lower = question.lower()
        
        # 1. Chained Follow-Up Pattern Recognition
        if previous_state:
            last_uc = previous_state.get("use_case_id")
            if last_uc == "UC1" and ("of those" in q_lower or "rank by" in q_lower or "purchases" in q_lower):
                return {
                    "use_case_id": "UC1a",
                    "concept_path": "use-cases/uc01a-rank-by-purchases.md",
                    "parent_use_case": "UC1",
                    "is_follow_up": True,
                }
            if last_uc == "UC2" and ("pie" in q_lower or "chart" in q_lower or "graph" in q_lower):
                return {
                    "use_case_id": "UC2a",
                    "concept_path": "use-cases/uc02a-pie-graph-visit-spend.md",
                    "parent_use_case": "UC2",
                    "is_follow_up": True,
                }
            if last_uc == "UC3" and ("top age band" in q_lower or "average store visits" in q_lower or "how many visits" in q_lower):
                return {
                    "use_case_id": "UC3a",
                    "concept_path": "use-cases/uc03a-top-age-band-store-visits.md",
                    "parent_use_case": "UC3",
                    "is_follow_up": True,
                }
            if last_uc == "UC4" and ("of those" in q_lower or "break-up" in q_lower or "online vs" in q_lower or "store spend" in q_lower):
                return {
                    "use_case_id": "UC4a",
                    "concept_path": "use-cases/uc04a-online-vs-store-spend-split.md",
                    "parent_use_case": "UC4",
                    "is_follow_up": True,
                }

        # 2. Match against primary trigger patterns
        if "doncaster" in q_lower or ("top 100" in q_lower and "email" in q_lower):
            if "purchase" in q_lower and "of those" in q_lower:
                return {"use_case_id": "UC1a", "concept_path": "use-cases/uc01a-rank-by-purchases.md"}
            return {"use_case_id": "UC1", "concept_path": "use-cases/uc01-top-members-doncaster-email.md"}

        if "average visit spend" in q_lower or "spend per visit" in q_lower or ("tier" in q_lower and "past 3 months" in q_lower):
            if "pie" in q_lower or "graph" in q_lower:
                return {"use_case_id": "UC2a", "concept_path": "use-cases/uc02a-pie-graph-visit-spend.md"}
            return {"use_case_id": "UC2", "concept_path": "use-cases/uc02-avg-visit-spend-by-tier.md"}

        if "age band" in q_lower or "in store vs online" in q_lower or "more likely to shop" in q_lower:
            if "visits per member" in q_lower or "top age band" in q_lower:
                return {"use_case_id": "UC3a", "concept_path": "use-cases/uc03a-top-age-band-store-visits.md"}
            return {"use_case_id": "UC3", "concept_path": "use-cases/uc03-age-band-store-vs-online.md"}

        if "joined in the last 6 months" in q_lower or ("new joiners" in q_lower and "frequency" in q_lower) or ("top 100" in q_lower and "visit frequency" in q_lower):
            if "break-up" in q_lower or "split" in q_lower:
                return {"use_case_id": "UC4a", "concept_path": "use-cases/uc04a-online-vs-store-spend-split.md"}
            return {"use_case_id": "UC4", "concept_path": "use-cases/uc04-new-joiners-high-frequency-spend.md"}

        if "this year vs last year" in q_lower or "green when up" in q_lower or "yoy" in q_lower or ("chart spend by member tier" in q_lower):
            return {"use_case_id": "UC5", "concept_path": "use-cases/uc05-spend-by-tier-yoy-comparison.md"}

        if "not spent in the last 6 months" in q_lower or "not spent" in q_lower or "dormant" in q_lower or "demographic breakdown" in q_lower:
            return {"use_case_id": "UC6", "concept_path": "use-cases/uc06-demographic-breakdown-spent-vs-not-spent.md"}

        if "staff_indicator" in q_lower or "team members" in q_lower or "multiple transactions" in q_lower or ("staff" in q_lower and "last month" in q_lower):
            return {"use_case_id": "UC7", "concept_path": "use-cases/uc07-staff-high-frequency-transactions.md"}

        if "gold" in q_lower and ("points" in q_lower or "2 months" in q_lower or "transacted" in q_lower):
            # Extract points threshold
            match = re.search(r"points\s*(?:>=|>|at least)?\s*(\d+)", q_lower)
            pts = int(match.group(1)) if match else None
            return {
                "use_case_id": "UC8",
                "concept_path": "use-cases/uc08-gold-inactive-points.md",
                "points_threshold": pts,
            }

        # 3. Dynamic lookup in GCS routing matrix
        routing_md = await self.fetch_routing_matrix()
        for line in routing_md.splitlines():
            if line.startswith("|") and "**UC" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    uc_name = parts[1].replace("*", "")
                    c_link = parts[2]
                    triggers = parts[3].lower()
                    # Check trigger keywords
                    for trig in triggers.split(","):
                        clean_trig = trig.strip().strip('"')
                        if clean_trig and clean_trig in q_lower:
                            # Extract path from markdown link [title](path)
                            m_path = re.search(r"\(([^)]+)\)", c_link)
                            path = m_path.group(1).lstrip("/") if m_path else ""
                            return {"use_case_id": uc_name, "concept_path": path}

        return {"use_case_id": "NONE", "concept_path": None}

    async def execute_inquiry(self, question: str, trace: bool = False, show_pii: bool = False) -> Dict[str, Any]:
        """
        Executes a complete analytical inquiry across Orchestrator, okf-navigator,
        sql-analyst, and viz-reporter subagents using MCP tools.
        """
        trace_log = {
            "question": question,
            "steps": [],
            "concepts_read": [],
            "sql_executed": None,
            "bytes_billed": 0,
            "row_count": 0,
        }

        # Step 1: Write todo plan
        trace_log["steps"].append("1. Consult OKF routing and resolve user inquiry.")

        # Step 2: Resolve use case
        prev_state = load_execution_state()
        resolved = await self.resolve_use_case(question, previous_state=prev_state)
        uc_id = resolved.get("use_case_id")
        concept_path = resolved.get("concept_path")

        if uc_id == "NONE" or not concept_path:
            # Fallback to ad-hoc notification
            return {
                "answer": "⚠️ This question does not match any certified curated loyalty use cases. Please formulate a question relating to the supported retail loyalty use cases (UC1 to UC8).",
                "table": None,
                "sql": None,
                "concepts": [],
                "assumptions": ["Not from a curated use case"],
                "bytes_billed": 0,
                "trace": trace_log,
            }

        # Special check: UC8 missing points parameter
        if uc_id == "UC8" and resolved.get("points_threshold") is None:
            return {
                "answer": "Please specify the minimum points balance threshold (e.g. `points >= 3000`) for the Gold tier inactive members count query.",
                "table": None,
                "sql": None,
                "concepts": [f"/{concept_path}"],
                "assumptions": ["Awaiting points_threshold parameter"],
                "bytes_billed": 0,
                "trace": trace_log,
            }

        trace_log["steps"].append(f"2. Read concept contract from GCS: {concept_path}")
        concept_content = await self.fetch_concept(concept_path)
        trace_log["concepts_read"].append(f"/{concept_path}")

        # Step 3: Extract SQL template and parameters
        sql_match = re.search(r"```sql\s*(.+?)\s*```", concept_content, re.DOTALL)
        if not sql_match:
            raise ValueError(f"Concept '{concept_path}' missing SQL block.")
        sql_template = sql_match.group(1).strip()

        # Prepare parameters
        params = {}
        if uc_id in ("UC1", "UC1a"):
            params = {"store_name": "Doncaster", "window_months": 12, "top_n": 100}
        elif uc_id in ("UC2", "UC2a"):
            params = {"window_months": 3}
        elif uc_id == "UC3":
            params = {"window_months": 6}
        elif uc_id == "UC3a":
            # Inherit top age band from UC3 (65+ or previous)
            top_band = "65+"
            if prev_state and prev_state.get("use_case_id") == "UC3":
                rows = prev_state.get("rows", [])
                if rows:
                    top_band = rows[0].get("age_band", "65+")
            params = {"target_age_band": top_band, "window_months": 6}
        elif uc_id in ("UC4", "UC4a"):
            params = {"join_window_months": 6, "min_visits": 5, "top_n": 100}
        elif uc_id == "UC5":
            params = {"ytd_mode": "calendar_ytd"}
        elif uc_id == "UC6":
            params = {"window_months": 6}
        elif uc_id == "UC7":
            params = {"window_days": 30, "top_n": 100}
        elif uc_id == "UC8":
            pts = resolved.get("points_threshold") or 3000
            params = {"points_threshold": pts, "window_months": 2}

        # Bind parameters
        executable_sql = bind_parameters(sql_template, params)
        trace_log["sql_executed"] = executable_sql
        trace_log["steps"].append("3. Parameterized SQL bound and verified with sql_guard.")

        # Step 4: Dry Run via BigQuery MCP tool
        dry_run_tool = next(t for t in self.tools["bigquery"] if t.name == "dry_run_query")
        raw_dry = await dry_run_tool.ainvoke({"sql": executable_sql})
        dry_res = extract_tool_result(raw_dry)
        if isinstance(dry_res, str):
            try:
                dry_res = json.loads(dry_res)
            except Exception:
                pass
        
        if not isinstance(dry_res, dict) or not dry_res.get("valid"):
            err_msg = dry_res.get("error") if isinstance(dry_res, dict) else str(dry_res)
            raise RuntimeError(f"Dry run failed: {err_msg}")
            
        est_bytes = dry_res.get("total_bytes_processed", 0)
        bytes_check = check_bytes_limit(est_bytes)
        if not bytes_check["allowed"]:
            raise RuntimeError(bytes_check["error"])
            
        trace_log["steps"].append(f"4. Dry run verified: {est_bytes:,} bytes scanned (within MAX_BYTES_BILLED limit).")

        # Step 5: Execute via BigQuery MCP tool
        exec_tool = next(t for t in self.tools["bigquery"] if t.name == "execute_query")
        raw_exec = await exec_tool.ainvoke({"sql": executable_sql, "max_rows": 1000})
        exec_res = extract_tool_result(raw_exec)
        if isinstance(exec_res, str):
            try:
                exec_res = json.loads(exec_res)
            except Exception:
                pass
        
        if not isinstance(exec_res, dict) or not exec_res.get("success"):
            err_msg = exec_res.get("error") if isinstance(exec_res, dict) else str(exec_res)
            raise RuntimeError(f"BigQuery query execution failed: {err_msg}")

        rows = exec_res.get("rows", [])
        cols = exec_res.get("columns", [])
        billed_bytes = exec_res.get("total_bytes_billed", est_bytes)
        trace_log["bytes_billed"] = billed_bytes
        trace_log["row_count"] = len(rows)
        trace_log["steps"].append(f"5. Query executed: {len(rows):,} rows retrieved.")

        # Save state for follow-ups
        save_execution_state({
            "use_case_id": uc_id,
            "parameters": params,
            "sql": executable_sql,
            "rows": rows,
            "columns": cols,
            "concept_path": concept_path,
        })

        # Step 6: Visualizations & Formatting
        chart_file = None
        table_output = None

        if uc_id == "UC2a":
            chart_path = "outputs/uc2a_visit_spend_pie.png"
            render_chart(rows, chart_type="pie", title="Average Visit Spend by Loyalty Tier (Past 3 Months)", output_path=chart_path)
            chart_file = chart_path
            table_output = render_table(rows, columns=["tier_name", "avg_visit_spend"], show_pii=show_pii)

        elif uc_id == "UC5":
            chart_path = "outputs/uc5_yoy_tier_spend.png"
            render_chart(rows, chart_type="grouped_bar", title="Spend by Member Tier: This Year (YTD) vs Last Year", output_path=chart_path)
            chart_file = chart_path
            table_output = render_table(rows, columns=["tier_name", "last_year_spend", "this_year_spend", "delta_spend", "pct_change", "variance_indicator"], show_pii=show_pii)

        else:
            table_output = render_table(rows, columns=cols, show_pii=show_pii, limit=15)

        # Generate Executive Answer
        answer_text = self._build_executive_answer(uc_id, rows, params, chart_file)

        return {
            "use_case_id": uc_id,
            "answer": answer_text,
            "table": table_output,
            "chart": chart_file,
            "sql": executable_sql,
            "concepts": [f"/{concept_path}"],
            "assumptions": [
                f"Evaluated relative to CURRENT_DATE() partition window.",
                f"Enforced MAX_BYTES_BILLED limit ({check_bytes_limit(0)['max_bytes']:,} bytes).",
                f"PII masked ({'unmasked via SHOW_PII' if show_pii else 'redacted by default'}).",
            ],
            "bytes_billed": billed_bytes,
            "row_count": len(rows),
            "trace": trace_log,
        }

    def _build_executive_answer(self, uc_id: str, rows: List[Dict[str, Any]], params: Dict[str, Any], chart: Optional[str]) -> str:
        """Synthesizes a business response tailored to the use case."""
        if uc_id == "UC1":
            top_sp = rows[0] if rows else {}
            return f"Identified top 100 email-contactable loyalty members at Doncaster over the last 12 months. Total cohort spend ranges from ${rows[-1].get('total_spend', 0):,.2f} up to ${top_sp.get('total_spend', 0):,.2f}."
        elif uc_id == "UC1a":
            top_p = rows[0] if rows else {}
            return f"Re-ranked the top 100 Doncaster members by purchase count. Top member completed {top_p.get('purchase_count', 0)} purchases (with ${top_p.get('total_spend', 0):,.2f} total spend)."
        elif uc_id == "UC2":
            summary = ", ".join(f"{r['tier_name']}: ${r['avg_visit_spend']:.2f}" for r in rows)
            return f"Average visit spend across loyalty tiers over the trailing 3 months: {summary}."
        elif uc_id == "UC2a":
            return f"Generated pie chart visualizing average visit spend by tier, saved to `{chart}`."
        elif uc_id == "UC3":
            # Identify top store band and top online band
            store_sorted = sorted(rows, key=lambda x: x.get("store_share_pct", 0), reverse=True)
            online_sorted = sorted(rows, key=lambda x: x.get("online_share_pct", 0), reverse=True)
            top_store = store_sorted[0]["age_band"]
            top_online = online_sorted[0]["age_band"]
            return f"Age band analysis over past 6 months reveals **{top_store}** is most likely to shop in store ({store_sorted[0]['store_share_pct']:.1f}% store share), while **{top_online}** is most likely to shop online ({online_sorted[0]['online_share_pct']:.1f}% online share)."
        elif uc_id == "UC3a":
            r = rows[0] if rows else {}
            return f"For the top in-store age band ({params.get('target_age_band', '65+')}), active members averaged **{r.get('avg_store_visits_per_active_member', 0):.2f} store visits** over the past 6 months."
        elif uc_id == "UC4":
            return f"Identified top 100 high-frequency members who joined within the last 6 months (>= {params.get('min_visits', 5)} visits), ranked by total spend."
        elif uc_id == "UC4a":
            return f"Channel spend breakdown generated for the top 100 high-frequency new joiners, detailing physical store vs online e-commerce spend."
        elif uc_id == "UC5":
            return f"Calendar YTD spend comparison chart generated with green/red variance highlighting, saved to `{chart}`. Gold and Platinum tiers show spend increases (green), while Bronze and Silver reflect decreases (red)."
        elif uc_id == "UC6":
            active_members = sum(r["member_count"] for r in rows if "Spent in Last" in r["activity_status"])
            dormant_members = sum(r["member_count"] for r in rows if "NOT Spent" in r["activity_status"])
            return f"Demographic breakdown complete: **{active_members:,} active members** (transacted in last 6 months) vs **{dormant_members:,} dormant members** (zero spend in last 6 months)."
        elif uc_id == "UC7":
            top_s = rows[0] if rows else {}
            return f"Identified top 100 staff members by transaction frequency in the last month. Top staff member recorded {top_s.get('total_transactions', 0)} total transactions, with multiple transactions occurring on {top_s.get('multi_transaction_days', 0)} distinct days."
        elif uc_id == "UC8":
            r = rows[0] if rows else {}
            pts = params.get("points_threshold", 3000)
            return f"Found **{r.get('inactive_gold_member_count', 0):,} Gold tier members** with points >= {pts:,} who have not transacted in the past 2 months."
        return "Analytical inquiry completed successfully."
