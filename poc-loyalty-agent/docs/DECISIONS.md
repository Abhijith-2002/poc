# Architectural Decision Records (ADRs)

This document records the key architectural choices, trade-offs, and design rationale for the Retail Loyalty OKF Deep Agent POC.

---

## ADR 001: OKF Concept Type for Retail Analytics Use Cases
- **Date**: 2026-11-03
- **Context**: OKF v0.2 introduces §10 "Attested Computation" (`type: Attested Computation`) with `runtime`, `parameters`, `executor`, and `attester`. We evaluated whether to use `type: Attested Computation` or a specialized `type: Use Case` for our retail loyalty analytics use cases (UC1–UC8).
- **Decision**: We adopt `type: Use Case` with Attested Computation parameters and metadata extensions.
- **Rationale**:
  - OKF frontmatter `type` is explicitly an open vocabulary; consumers must tolerate unknown and domain-specific types.
  - While an Attested Computation is tailored for automated metric computation receipts and cryptographically or deterministically attested scripts, our use cases represent end-to-end analytical contracts that include:
    - User intent and example natural language questions.
    - Parameter contracts (`@store_name`, `@window_months`, `@points_threshold`, etc.).
    - Canonical SQL queries with partition filters and CTEs.
    - Chained follow-up variants (e.g. UC1a, UC2a, UC3a, UC4a).
    - Visualization specifications (e.g. UC2a pie, UC5 colored grouped bar chart).
    - Validation expectations and result-interpretation notes.
  - Using `type: Use Case` allows us to cleanly encompass these analytical dimensions while adopting the exact parameter schema and runtime specifications of Attested Computations (`runtime: bigquery`, `parameters: [...]`, `attester`).

---

## ADR 002: FastMCP Implementation for Google Cloud Storage OKF Server
- **Date**: 2026-11-03
- **Context**: The agent needs to read OKF bundle files stored in Google Cloud Storage (`gs://$OKF_BUCKET/$OKF_PREFIX`). The prompt instructs: if no maintained, lightweight GCS MCP server exists, write a minimal one in `mcp_servers/gcs_okf_server/` (FastMCP) exposing ONLY `list_objects(prefix)`, `read_object(path)`, `read_objects_batch(paths)` for the bundle bucket, read-only.
- **Decision**: Implement a purpose-built FastMCP server in `mcp_servers/gcs_okf_server/server.py` using `mcp.server.fastmcp` (or Python MCP SDK) that is strictly read-only and restricted to the configured OKF bucket and prefix.
- **Rationale**:
  - Eliminates unnecessary external dependencies and broad permissions.
  - Exposes precisely the tools needed:
    1. `list_objects(prefix: str)`: Lists available concepts in the bundle.
    2. `read_object(path: str)`: Reads a single Markdown concept with YAML frontmatter.
    3. `read_objects_batch(paths: list[str])`: Fetches multiple related concepts in one network call, reducing latency for complex graph traversals (e.g., use case + glossary + metric + table concepts).
  - Strictly prevents any write, delete, or cross-bucket access, adhering to zero-trust principles.

---

## ADR 003: BigQuery MCP Server Integration & Read-Only Guardrails
- **Date**: 2026-11-03
- **Context**: The agent needs to execute BigQuery queries via MCP without importing `google-cloud-bigquery` in the agent runtime. Queries must be strictly read-only, dry-run verified, capped at `MAX_BYTES_BILLED`, and row-limited.
- **Decision**: Implement a FastMCP BigQuery server in `mcp_servers/bq_server/server.py` exposing:
  1. `execute_query(sql: str, max_rows: int = 1000)`: Runs query with `maximum_bytes_billed` limit and returns tabular results.
  2. `dry_run_query(sql: str)`: Performs BigQuery dry run returning estimated bytes processed, validity, and schema without incurring execution costs.
  3. `list_tables(dataset: str)`: Lists tables and views.
  4. `describe_table(table_id: str)`: Returns column schema and partition metadata.
- **Rationale**:
  - Guarantees complete separation: `agent/` interacts with BigQuery solely through MCP tool protocols over stdio/HTTP.
  - Server-side and client-side defense-in-depth: queries are checked by `sqlglot` for syntax and prohibited statements (DROP, INSERT, UPDATE, DELETE, ALTER, etc.) before reaching the API.

---

## ADR 004: Multi-Agent Hierarchy with `create_deep_agent`
- **Date**: 2026-11-03
- **Context**: Answering retail loyalty questions requires discovering concepts in OKF, selecting canonical SQL, binding parameters, validating queries, executing against BigQuery, and rendering charts/tables.
- **Decision**: Structured multi-agent workflow using LangChain `deepagents` (`create_deep_agent`):
  1. **Orchestrator**: Maintains the high-level task plan (todo list), receives user questions, coordinates sub-agents, caches bundle files in the virtual filesystem, and synthesizes the final response.
  2. **`okf-navigator` sub-agent**: Reads OKF bundle from GCS via GCS MCP tools. Discovers the matching use-case concept, reads linked glossary and metric concepts, extracts parameters, and prepares the execution brief.
  3. **`sql-analyst` sub-agent**: Interacts with the BigQuery MCP server. Verifies SQL via `sql_guard`, executes dry runs, checks byte limits, runs the query, and stores tabular results.
  4. **`viz-reporter` sub-agent**: Consumes execution results and generates formatted markdown tables or charts (`outputs/*.png`) using local tools (`render_chart`, `render_table`).
- **Rationale**:
  - Context isolation prevents prompt clutter and context degradation.
  - Specialized tools per sub-agent minimize tool confusion and improve reliability.

---

## ADR 005: State Persistence for Chained Follow-Ups (UC1a, UC2a, UC3a, UC4a)
- **Date**: 2026-11-03
- **Context**: Follow-up questions (e.g., UC1a "Of those 100, rank by number of purchases" or UC2a "Provide a pie graph of UC2") depend on the previous execution state.
- **Decision**: Persist execution context (last use-case ID, bound parameters, query result summary, and intermediate data files) into the `deepagents` virtual filesystem (`/tmp/loyalty_state/last_execution.json`).
- **Rationale**:
  - Enables sub-agents and follow-up queries to seamlessly reuse prior results without re-querying or re-scanning partitions unnecessarily.
  - Supports chained CTE variants defined directly in the OKF concepts.

---

## ADR 006: PII Masking and Data Protection
- **Date**: 2026-11-03
- **Context**: Retail loyalty data contains customer identifiers (names, emails, dates of birth).
- **Decision**: By default, mask email addresses (e.g. `j***@d***.com`) and names in all displayed agent output and markdown artifacts. Only expose unmasked PII when the environment variable `SHOW_PII=true` is explicitly set. For campaign export use cases (e.g., UC1 Doncaster email campaign), write an unmasked export file to `outputs/uc1_doncaster_campaign.csv` only when `SHOW_PII=true` or write a masked preview.
- **Rationale**:
  - Enforces privacy-by-design for production-grade analytical agents.

