---
type: Convention
title: SQL Authoring Style
description: Read-only query standards, Common Table Expressions (CTEs), parameterization syntax, and partition filtering.
tags:
  - conventions
  - sql
  - standards
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
---

# SQL Authoring Style

## Core Rules
1. **Strictly Read-Only**: Queries must begin with `SELECT` or `WITH`. Prohibit `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `DROP`, `ALTER`, `CREATE`, or multiple semicolon-separated statements.
2. **Mandatory Partition Filters**: Every query touching `fact_transaction` or `vw_member_transactions` MUST include a `transaction_date` filter in its `WHERE` clause.
3. **Parameterization**: Parameterized queries use `@param_name` format (or `${PROJECT}.${DATASET}` project-qualified dataset anchors).
4. **Common Table Expressions (CTEs)**: Structure multi-step logic using readable CTEs (`WITH cohort AS (...), aggregated AS (...) SELECT ...`).
5. **Deterministic Row Limits**: All unaggregated or ranking queries must end with an explicit `LIMIT` (e.g. `LIMIT 100`).

