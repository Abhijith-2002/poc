---
type: Use Case
use_case_id: UC2
title: Average visit spend per member broken down by member tier past 3 months
description: Calculates the average spend per shopping visit across each loyalty tier over the trailing 3 months.
runtime: bigquery
parameters:
  - name: window_months
    type: integer
    default: 3
    required: true
    description: "Trailing months window relative to current date."
output_columns:
  - name: tier_name
    type: string
  - name: avg_visit_spend
    type: float
  - name: total_spend
    type: float
  - name: visit_count
    type: integer
visualization: none
validation:
  min_rows: 4
  max_rows: 4
  assertions:
    - "avg_visit_spend > 0"
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/datasets/loyalty_poc/tables/dim_member.md"
  - "/datasets/loyalty_poc/tables/dim_member_tier.md"
  - "/metrics/avg-visit-spend.md"
  - "/glossary/tier.md"
---

# UC2: Average Visit Spend by Member Tier (Past 3 Months)

## 1. Intent & Example Questions
- "What is the average visit spend per member, broken down by member tier, for the past 3 months?"
- "Show average spend per visit by tier over the last 3 months."
- "Break down basket spend per visit across Bronze, Silver, Gold, Platinum over the last 90 days."

## 2. Parameters & Defaults
- `@window_months` (INT64, default: `3`): Number of trailing months.

## 3. Business Rules & Definitions
- **Visit Grain**: Consistent with [Visit](/glossary/visit.md) and [Average Visit Spend](/metrics/avg-visit-spend.md), each distinct completed transaction represents a shopping visit occasion.
- **Tier Grouping**: Grouped by [Loyalty Tier](/glossary/tier.md) (`Bronze`, `Silver`, `Gold`, `Platinum`).
- **Date Partition**: Filters `transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)`.

## 4. Canonical BigQuery SQL Template
```sql
SELECT
  m.tier_name,
  ROUND(SAFE_DIVIDE(SUM(t.total_amount), COUNT(t.transaction_id)), 2) AS avg_visit_spend,
  ROUND(SUM(t.total_amount), 2) AS total_spend,
  COUNT(t.transaction_id) AS visit_count
FROM `${PROJECT}.${DATASET}.fact_transaction` t
JOIN `${PROJECT}.${DATASET}.dim_member` m ON t.member_id = m.member_id
WHERE t.transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)
GROUP BY m.tier_name
ORDER BY avg_visit_spend DESC;
```

## 5. Chained / Follow-Up Variants
- Followed by [UC2a: Pie Graph of Visit Spend](/use-cases/uc02a-pie-graph-visit-spend.md) which renders this tabular output into a visual pie chart.

## 6. Output Format & Visualization Specification
- **Visualization**: `none` (tabular summary table for UC2).
- Returns 4 rows corresponding to the 4 loyalty tiers.

## 7. Edge Cases, Pitfalls & Interpretation Notes
- Joining via `dim_member` ensures that current tier attribution is reflected.
- Using `SAFE_DIVIDE` prevents division-by-zero errors in empty or sparse partitions.

