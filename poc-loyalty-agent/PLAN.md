# Implementation Plan: Retail Loyalty OKF Deep Agent POC

## Overview & Objectives
Build an autonomous, end-to-end Proof of Concept (POC) featuring a LangChain **deepagents** agent (`create_deep_agent`) that answers retail-loyalty analytics questions for 12 canonical use cases (UC1 to UC8, including follow-up variants 1a, 2a, 3a, 4a). The agent operates strictly via:
1. **Model Context Protocol (MCP)** for reading an **Open Knowledge Format (OKF) v0.2 bundle** stored in Google Cloud Storage.
2. **BigQuery MCP Server** for executing read-only SQL queries with dry-run cost controls, query guardrails, and partition filtering.
3. Local rendering and formatting tools for tabular data and visualizations (UC2a pie chart, UC5 color-highlighted grouped bar chart).

---

## Phase Breakdown & Execution Gates

### Phase 1: Synthetic BigQuery Datasets & Data Generation
- **Target**: Generate ~24 months of rich, realistic synthetic retail loyalty data ending at current date.
- **Key Characteristics**:
  - ~50,000 members, ~1.5M transactions across stores and online.
  - Pareto spend distribution, holiday seasonality (peaking Nov–Dec).
  - Deliberately supports every use case:
    - UC1/UC1a: Doncaster store volume with >= 100 email-contactable high spenders.
    - UC2/UC2a: 3 months visit spend across Bronze, Silver, Gold, Platinum tiers.
    - UC3/UC3a: Age band in-store vs online propensity with marked differences across bands.
    - UC4/UC4a: Members joined in the last 6 months with high visit frequency.
    - UC5: Calendar YTD spend this year vs same period last year showing both increases and decreases across tiers.
    - UC6: Dormant members (no spend in last 6 months, ~5%) vs active members, broken down by demographics.
    - UC7: Staff members (`staff_indicator='Y'`, ~3%) with multiple transactions on the same day in the last month.
    - UC8: Inactive Gold members with varying points balances (>= runtime threshold) and no transactions in 2 months.
- **Schema & Tables**:
  - `dim_member`: PK `member_id`, names, email, opt-in flags, demographics, join_date, tier, points_balance, staff_indicator, status.
  - `dim_member_tier`: `tier_id`, `tier_name`, spend/points thresholds, benefits.
  - `dim_store`: `store_id`, `store_name` ('Doncaster' + 15 stores + 'ONLINE'), state, region, channel_type.
  - `fact_transaction`: `transaction_id`, `member_id`, `store_id`, `channel`, `transaction_ts`, `transaction_date`, `total_amount`, `discount_amount`, `items_count`, `points_earned`, `payment_type`. Partitioned by `transaction_date`, clustered by `member_id`, `store_id`.
  - `fact_transaction_line`: line items per transaction with product categories.
  - `fact_points_ledger`: member points accrual, redemption, and adjustment events.
  - `dim_date`: date dimension table.
  - View `vw_member_transactions`: denormalized transaction + member + store + tier view.
- **Scripts**:
  - `scripts/generate_data.py`: Generates data using `faker` and `numpy` (fixed seed: 42) directly to local Parquet files.
- **Verification Gate**:
  - Assert row counts, schema validity, referential integrity between fact and dim tables, and non-empty results for all 12 use case queries directly on the Parquet/BQ dataset.

---

### Phase 2: OKF v0.2 Knowledge Bundle (`okf_bundle/`)
- **Target**: Create a fully compliant OKF v0.2 bundle representing the semantic layer and analytical contracts.
- **Structure**:
  - `index.md`: Root index with `okf_version: "0.2"`, directory overview, and navigation roadmap for agents.
  - `log.md`: Chronological changelog with ISO date headings.
  - `datasets/loyalty_poc/index.md`: Dataset overview and data architecture.
  - `datasets/loyalty_poc/tables/*.md`: Markdown concept for every table (schema, grain, PK/FK, column definitions, partitioning, join paths, cost advice).
  - `datasets/loyalty_poc/views/vw_member_transactions.md`: View definition and column mappings.
  - `glossary/*.md`: Business definitions (spend, visit, purchase, contactable, active/inactive, high frequency, staff indicator, age bands).
  - `metrics/*.md`: Canonical metric formulas and SQL expressions (total spend, average visit spend, purchase count, visit frequency).
  - `conventions/*.md`: Date windows (rolling relative to `CURRENT_DATE()`, calendar YTD), SQL standards, PII policies, visualization standards.
  - `use-cases/index.md`: Catalog of all 12 use cases with links.
  - `use-cases/uc01-top-members-doncaster-email.md` to `uc08-gold-inactive-points.md`: Full canonical analytical contracts with parameters, canonical SQL templates, chained variants, output specs, and validation assertions.
  - `routing/question-routing.md`: Natural-language trigger phrases, synonym maps, and disambiguation rules.
- **Verification Gate**:
  - Conformance test validating YAML frontmatter, non-empty `type`, root `okf_version: "0.2"`, absence of frontmatter in sub-indexes, broken link verification, and SQL syntax checks.

---

### Phase 3: Load & Validate Pipeline
- **Scripts**:
  - `scripts/create_bq_assets.py`: Creates BigQuery dataset `loyalty_poc`, tables with partitioning/clustering and descriptions, view `vw_member_transactions`, and loads data from Parquet files.
  - `scripts/build_okf_bundle.py`: Programmatically generates/updates table concepts from live BigQuery metadata to eliminate documentation drift.
  - `scripts/validate_okf.py`: Runs end-to-end bundle validation and BigQuery dry-runs for every use case SQL template.
  - `scripts/upload_to_gcs.py`: Uploads the validated bundle to `gs://$OKF_BUCKET/$OKF_PREFIX`.
- **Verification Gate**:
  - Dry run of all 12 SQL queries against BigQuery passes with 0 syntax errors, valid byte estimates, and schema validation.
  - Bundle uploaded to GCS and verified with listing.

---

### Phase 4: MCP Servers & Configuration
- **Target**: Provide zero-trust, read-only MCP access to GCS and BigQuery.
- **Components**:
  - `mcp_servers/gcs_okf_server/server.py`: FastMCP server exposing `list_objects(prefix)`, `read_object(path)`, `read_objects_batch(paths)`.
  - `mcp_servers/bq_server/server.py`: FastMCP server exposing `execute_query(sql, max_rows)`, `dry_run_query(sql)`, `list_tables(dataset)`, `describe_table(table_id)`.
  - `config/mcp_servers.json`: Standardized server configuration (command, args, env).
  - `agent/mcp_clients.py`: Client loader using `langchain-mcp-adapters` (`MultiServerMCPClient`) or direct MCP client protocol, with startup tool discovery and smoke test.
- **Verification Gate**:
  - Smoke test: successfully list GCS bundle root over MCP, read `index.md`, execute `SELECT 1` and dry-run a query via BigQuery MCP.

---

### Phase 5: The Deep Agent Implementation
- **Target**: Autonomous reasoning agent built with `deepagents` (`create_deep_agent`).
- **Architecture**:
  - **Orchestrator**: Maintains plan/todo list, discovers use cases, delegates to specialized subagents, enforces response format.
  - **`okf-navigator` sub-agent**: Interacts with GCS MCP to resolve user intent, extract canonical SQL templates, bind parameters, and produce an execution brief.
  - **`sql-analyst` sub-agent**: Interacts with BigQuery MCP, runs `sql_guard` -> `dry_run_query` -> `execute_query`, verifies result shape, and caches results for follow-ups.
  - **`viz-reporter` sub-agent**: Renders markdown tables, generates charts (`outputs/*.png` for UC2a pie and UC5 green/red grouped bars).
  - **Local Tools (`agent/tools_local.py`)**: `render_chart`, `render_table`, `bind_parameters`, `sql_guard`.
  - **Guardrails (`agent/guardrails.py`)**: AST parsing (rejecting DDL/DML/multi-statement), byte limit enforcement (`MAX_BYTES_BILLED`), row caps, PII masking (`SHOW_PII` flag).
  - **CLI Interface (`agent/main.py`)**: Interactive streaming chat loop + `--question` one-shot mode + `--trace` telemetry output.
- **Verification Gate**:
  - Verify that the agent correctly answers all 12 questions with cited OKF concepts, formatted outputs, and charts where specified.

---

### Phase 6: Tests, Evals & Golden Comparisons
- **Test Suites**:
  - `tests/test_sql_guard.py`: Unit tests verifying that DDL, DML, multi-statement queries, and unauthorized comments are blocked, while CTEs and SELECTs are permitted.
  - `tests/test_okf_conformance.py`: Unit tests validating OKF v0.2 structure, frontmatter schemas, and relative links.
  - `tests/test_use_case_routing.py`: Eval of 30+ varied questions to verify deterministic routing to the correct use case ID (and handling out-of-scope queries).
  - `tests/test_golden_results.py`: Compares agent execution numbers against canonical reference results.
  - `tests/e2e_runner.py`: End-to-end execution of all 12 questions across 3 conversational chains, generating `outputs/e2e_report.md`.
- **Verification Gate**:
  - 100% test pass rate across unit, routing, golden, and e2e evaluation suites.

---

### Phase 7: Documentation & Demo Readiness
- **Deliverables**:
  - `README.md`: 15-minute quickstart guide, environment configuration, assumptions, and extension guide.
  - `docs/ARCHITECTURE.md`: Complete architectural documentation with Mermaid sequence and component diagrams.
  - `docs/DEMO_SCRIPT.md`: Step-by-step transcript of the 12 questions with expected outputs.
  - `Makefile`: Single command convenience targets (`make data`, `make bq`, `make okf`, `make upload`, `make test`, `make agent`, `make all`).

---

## Progress Tracking & Status
- [x] Step 0: Research OKF v0.2 spec, MCP servers, and DeepAgents APIs.
- [x] Step 0: Write `docs/OKF_NOTES.md` and `docs/DECISIONS.md`.
- [x] Step 0: Write `PLAN.md`.
- [ ] Phase 1: Synthetic data generation and local Parquet creation.
- [ ] Phase 2: OKF v0.2 bundle authoring (`okf_bundle/`).
- [ ] Phase 3: BigQuery asset creation, validation, and GCS upload scripts.
- [ ] Phase 4: MCP servers (`gcs_okf_server`, `bq_server`) and client loader.
- [ ] Phase 5: Deep Agent graph, prompts, guardrails, and CLI runner.
- [ ] Phase 6: Test suites, routing evals, golden comparisons, and e2e report.
- [ ] Phase 7: README, Architecture docs, Demo script, and Makefile.

