---
type: Metric
title: Total Spend
description: Sum of all completed transaction amounts across a specified cohort and date partition window.
tags:
  - metric
  - revenue
  - spend
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
---

# Total Spend Metric

## Formula
$$\text{Total Spend} = \sum \text{total\_amount}$$

## Canonical BigQuery SQL Expression
```sql
ROUND(SUM(total_amount), 2)
```

## Filters & Governance
- Must always be bounded by a date range on the partitioned column:
  ```sql
  WHERE transaction_date BETWEEN @start_date AND @end_date
  ```
- Excludes transactions that have been fully refunded or reversed.

