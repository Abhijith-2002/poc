---
type: Metric
title: Average Visit Spend
description: Mean spend per visit occasion, calculated as total spend divided by total visits or transactions.
tags:
  - metric
  - basket-size
  - average
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/glossary/visit.md"
---

# Average Visit Spend

## Formula
$$\text{Average Visit Spend} = \frac{\sum \text{total\_amount}}{\text{Count of Visits}}$$

## Canonical BigQuery SQL Expression
```sql
ROUND(SAFE_DIVIDE(SUM(total_amount), COUNT(transaction_id)), 2)
```

## Dimensional Breakdown
In [UC2: Average Visit Spend by Tier](/use-cases/uc02-avg-visit-spend-by-tier.md), this metric is grouped by `tier_name` over the trailing 3 months (`DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH)`).

