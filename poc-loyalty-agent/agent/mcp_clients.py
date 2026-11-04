"""
agent/mcp_clients.py
Initializes Model Context Protocol (MCP) clients for GCS and BigQuery.
Enforces the strict constraint: NO direct imports of google-cloud-bigquery
or google-cloud-storage in the agent runtime. Reaches data strictly via MCP.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Union
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient


def extract_tool_result(raw_result: Any) -> Any:
    """
    Extracts underlying content or parsed JSON from LangChain MCP adapter tool responses.
    MCP tools return list of content dicts [{'type': 'text', 'text': '...'}] or raw values.
    """
    if isinstance(raw_result, list):
        if len(raw_result) == 0:
            return []
        if isinstance(raw_result[0], dict) and raw_result[0].get("type") == "text":
            text_blocks = [b.get("text", "") for b in raw_result if isinstance(b, dict) and b.get("type") == "text"]
            combined = "\n".join(text_blocks).strip()
            if combined.startswith("{") or combined.startswith("["):
                try:
                    return json.loads(combined)
                except Exception:
                    pass
            return combined
        return raw_result
    elif isinstance(raw_result, str):
        s = raw_result.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                return json.loads(s)
            except Exception:
                pass
        return raw_result
    elif isinstance(raw_result, dict):
        if raw_result.get("type") == "text" and "text" in raw_result:
            s = str(raw_result["text"]).strip()
            if s.startswith("{") or s.startswith("["):
                try:
                    return json.loads(s)
                except Exception:
                    pass
            return s
        return raw_result
    return raw_result


def load_mcp_server_config(config_path: str = "config/mcp_servers.json") -> Dict[str, Any]:
    """Loads MCP server configurations from JSON file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_path = config_path if os.path.isabs(config_path) else os.path.join(base_dir, config_path)
    if not os.path.exists(target_path):
        target_path = config_path
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"MCP server config not found at: {config_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    servers = data.get("mcpServers", {})
    resolved = {}
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_exec = sys.executable

    for name, s_cfg in servers.items():
        cmd = s_cfg.get("command", "python")
        if cmd in ("python", ".venv/bin/python"):
            cmd = py_exec
        args = [os.path.join(base_dir, a) if not os.path.isabs(a) else a for a in s_cfg.get("args", [])]
        resolved[name] = {
            "command": cmd,
            "args": args,
            "transport": s_cfg.get("transport", "stdio"),
            "env": {**os.environ, **s_cfg.get("env", {})},
        }
    return resolved


def create_mcp_client(config_path: str = "config/mcp_servers.json") -> MultiServerMCPClient:
    """Instantiates a MultiServerMCPClient configured for GCS and BigQuery."""
    server_configs = load_mcp_server_config(config_path)
    client = MultiServerMCPClient(server_configs)
    return client


async def get_categorized_tools(client: MultiServerMCPClient):
    """
    Discovers all tools across connected MCP servers and categorizes them
    for specialized sub-agents.
    """
    all_tools = await client.get_tools()
    gcs_tool_names = {"list_objects", "read_object", "read_objects_batch"}
    bq_tool_names = {"dry_run_query", "execute_query", "list_tables", "describe_table"}

    gcs_tools = [t for t in all_tools if t.name in gcs_tool_names]
    bq_tools = [t for t in all_tools if t.name in bq_tool_names]

    return {
        "all": all_tools,
        "gcs": gcs_tools,
        "bigquery": bq_tools,
    }


async def run_mcp_smoke_test(config_path: str = "config/mcp_servers.json"):
    """
    Executes Phase 4 smoke test:
      (1) Lists bundle root over MCP.
      (2) Reads index.md over MCP.
      (3) Runs SELECT 1 and dry-run query through BigQuery MCP tool.
    """
    print("=== Starting MCP Servers Smoke Test ===")
    client = create_mcp_client(config_path)
    tools = await get_categorized_tools(client)
    
    print(f"Discovered {len(tools['all'])} MCP tools:")
    for t in tools["all"]:
        desc = t.description.splitlines()[0] if t.description else ""
        print(f"  - [{t.name}] {desc}")

    # 1. Test GCS list_objects
    list_tool = next(t for t in tools["gcs"] if t.name == "list_objects")
    raw_bundle = await list_tool.ainvoke({"prefix": ""})
    bundle_res = extract_tool_result(raw_bundle)
    if isinstance(bundle_res, str):
        bundle_files = [line.strip() for line in bundle_res.splitlines() if line.strip()]
    elif isinstance(bundle_res, list):
        bundle_files = [x.get("text", x) if isinstance(x, dict) else str(x) for x in bundle_res]
    else:
        bundle_files = []

    print(f"\n[GCS MCP] list_objects found {len(bundle_files)} concepts.")
    assert "index.md" in bundle_files, "index.md not found in bundle root over MCP!"
    print("✓ GCS list_objects passed.")

    # 2. Test GCS read_object
    read_tool = next(t for t in tools["gcs"] if t.name == "read_object")
    raw_index = await read_tool.ainvoke({"path": "index.md"})
    index_content = extract_tool_result(raw_index)
    assert "okf_version: \"0.2\"" in str(index_content) or "okf_version: '0.2'" in str(index_content), "index.md missing okf_version declaration"
    print("✓ GCS read_object('index.md') passed.")

    # 3. Test BigQuery dry_run_query
    dry_run_tool = next(t for t in tools["bigquery"] if t.name == "dry_run_query")
    raw_dry = await dry_run_tool.ainvoke({"sql": "SELECT 1 AS test_col"})
    dry_res = extract_tool_result(raw_dry)
    assert dry_res.get("valid") is True, f"Dry run query failed: {dry_res}"
    print(f"✓ BigQuery dry_run_query passed. Engine: {dry_res.get('engine')}, Est. Bytes: {dry_res.get('total_bytes_processed')}")

    # 4. Test BigQuery execute_query
    exec_tool = next(t for t in tools["bigquery"] if t.name == "execute_query")
    raw_exec = await exec_tool.ainvoke({"sql": "SELECT 1 AS test_val", "max_rows": 10})
    exec_res = extract_tool_result(raw_exec)
    assert exec_res.get("success") is True, f"Execute query failed: {exec_res}"
    rows = exec_res.get("rows", [])
    assert len(rows) == 1 and rows[0].get("test_val") == 1, f"Unexpected result: {exec_res}"
    print(f"✓ BigQuery execute_query('SELECT 1') passed. Result: {rows}")

    print("\n=== All MCP Smoke Tests Passed Successfully! ===")


if __name__ == "__main__":
    asyncio.run(run_mcp_smoke_test())
