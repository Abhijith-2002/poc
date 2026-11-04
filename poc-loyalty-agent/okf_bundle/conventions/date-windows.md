---
type: Convention
title: Date Window Standards
description: Standardized rules for relative rolling time windows and year-over-year comparisons in BigQuery.
tags:
  - conventions
  - time-windows
  - dates
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
---

# Date Window Standards

## Standard Definitions
All analytical time windows are evaluated dynamically relative to `CURRENT_DATE()`:

1. **Last 12 Months**:
   ```sql
   transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
   ```
2. **Last 6 Months**:
   ```sql
   transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
   ```
3. **Past 3 Months**:
   ```sql
   transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH)
   ```
4. **Past 2 Months**:
   ```sql
   transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH)
   ```
5. **Last Month (Past 30 Days)**:
   ```sql
   transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
   ```
6. **This Year vs Last Year (Calendar YTD)**:
   - This Year: From `DATE_TRUNC(CURRENT_DATE(), YEAR)` through `CURRENT_DATE()`.
   - Last Year Same Period: From `DATE_SUB(DATE_TRUNC(CURRENT_DATE(), YEAR), INTERVAL 1 YEAR)` through `DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR)`.

