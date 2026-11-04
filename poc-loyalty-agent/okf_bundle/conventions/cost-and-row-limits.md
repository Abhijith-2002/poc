---
type: Convention
title: Cost and Row Limits
description: Execution guardrails including dry-run validation, maximum bytes billed, and row limit caps.
tags:
  - conventions
  - finops
  - guardrails
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
---

# Cost and Row Limits

## Guardrail Specifications
1. **Mandatory Dry Run**:
   - Before executing any BigQuery job, perform a dry run (`dry_run=True`) to estimate `total_bytes_processed`.
   - If estimated bytes exceed `MAX_BYTES_BILLED` (default: 100 MB / 104,857,600 bytes), abort execution and alert the user.
2. **Maximum Bytes Billed**:
   - Every live query job specifies `maximum_bytes_billed = MAX_BYTES_BILLED`.
3. **Maximum Rows Returned**:
   - Agent queries apply `MAX_ROWS = 1000` to prevent memory exhaustion and token bloat.

