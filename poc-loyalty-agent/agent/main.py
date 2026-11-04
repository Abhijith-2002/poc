#!/usr/bin/env python3
"""
agent/main.py
CLI interface and one-shot execution loop for the Retail Loyalty OKF Deep Agent.
Supports interactive chat, --question "..." one-shot mode, --trace telemetry output,
and --show-pii data unmasking.
"""

import argparse
import asyncio
import json
import os
import sys

from agent.graph import LoyaltyDeepAgent


def format_agent_response(result: dict) -> str:
    """Formats the agent response matching the required contract."""
    output_lines = [
        "## Executive Answer",
        result.get("answer", ""),
        "",
    ]

    if result.get("chart"):
        output_lines.extend([
            f"**Visualization Generated**: `![Chart]({result['chart']})`",
            "",
        ])

    if result.get("table"):
        output_lines.extend([
            "### Results",
            result["table"],
            "",
        ])

    if result.get("sql"):
        output_lines.extend([
            "### BigQuery SQL Executed",
            "```sql",
            result["sql"],
            "```",
            "",
        ])

    concepts = result.get("concepts", [])
    if concepts:
        output_lines.extend([
            "### OKF Concepts Cited",
            "\n".join(f"- `{c}`" for c in concepts),
            "",
        ])

    assumptions = result.get("assumptions", [])
    if assumptions:
        output_lines.extend([
            "### Assumptions & Governance",
            "\n".join(f"- {a}" for a in assumptions),
            "",
        ])

    output_lines.extend([
        "### Cost & Telemetry",
        f"- **Rows Scanned / Returned**: {result.get('row_count', 0):,}",
        f"- **Bytes Billed**: {result.get('bytes_billed', 0):,} bytes",
        "",
        "---",
    ])

    return "\n".join(output_lines)


async def async_main():
    parser = argparse.ArgumentParser(description="Retail Loyalty OKF Deep Agent CLI")
    parser.add_argument("--question", "-q", type=str, help="One-shot question to answer")
    parser.add_argument("--trace", action="store_true", help="Print and save detailed execution trace")
    parser.add_argument("--show-pii", action="store_true", help="Display unmasked customer PII (names, emails)")
    parser.add_argument("--config", default="config/mcp_servers.json", help="Path to MCP server configuration")
    args = parser.parse_args()

    print("=== Initializing Retail Loyalty Deep Agent (OKF v0.2 + BigQuery MCP) ===")
    agent = LoyaltyDeepAgent(config_path=args.config)
    await agent.initialize()
    print("✓ Deep Agent initialized with GCS and BigQuery MCP toolsets.\n")

    if args.question:
        # One-shot mode
        print(f"User: {args.question}\n")
        res = await agent.execute_inquiry(args.question, trace=args.trace, show_pii=args.show_pii)
        print(format_agent_response(res))

        if args.trace:
            trace_path = "outputs/last_trace.json"
            os.makedirs("outputs", exist_ok=True)
            with open(trace_path, "w", encoding="utf-8") as f:
                json.dump(res.get("trace", {}), f, indent=2)
            print(f"Trace saved to `{trace_path}`.")
        return

    # Interactive Chat Loop
    print("Welcome to the Retail Loyalty Analytics Assistant!")
    print("Type your questions below, or 'exit' / 'quit' to end.\n")

    while True:
        try:
            user_input = input("LoyaltyAgent > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Session terminated. Goodbye!")
                break

            print("\nThinking and executing...")
            res = await agent.execute_inquiry(user_input, trace=args.trace, show_pii=args.show_pii)
            print()
            print(format_agent_response(res))

            if args.trace:
                print(f"Trace telemetry: {json.dumps(res.get('trace', {}), indent=2)}")

        except (KeyboardInterrupt, EOFError):
            print("\nSession interrupted. Exiting.")
            break
        except Exception as e:
            print(f"\n❌ Error processing query: {e}\n")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()

