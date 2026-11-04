---
type: Use Case
use_case_id: UC2a
parent_use_case: "use-cases/uc02-avg-visit-spend-by-tier"
title: Pie Graph of Average Visit Spend by Tier
description: Visualizes the average visit spend per member across loyalty tiers as a pie chart.
runtime: bigquery
inputs_from_parent:
  - tier_name
  - avg_visit_spend
  - total_spend
visualization: pie
parameters:
  - name: window_months
    type: integer
    default: 3
    required: true
    description: "Trailing months inherited from UC2."
output_columns:
  - name: tier_name
    type: string
  - name: avg_visit_spend
    type: float
validation:
  min_rows: 4
  max_rows: 4
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/use-cases/uc02-avg-visit-spend-by-tier.md"
  - "/conventions/visualization-standards.md"
---

# UC2a: Provide a Pie Graph of UC2

## 1. Intent & Example Questions
- "Provide a pie graph of UC2."
- "Show me that breakdown as a pie chart."
- "Can you chart average visit spend by tier as a pie?"

## 2. Parameters & Defaults
- Reuses data and parameters from [UC2](/use-cases/uc02-avg-visit-spend-by-tier.md) (`@window_months = 3`).

## 3. Business Rules & Definitions
- Displays the proportion of average visit spend attributable to each loyalty tier.
- Slices correspond to Bronze, Silver, Gold, Platinum.

## 4. Canonical BigQuery SQL Template
```sql
SELECT
  m.tier_name,
  ROUND(SAFE_DIVIDE(SUM(t.total_amount), COUNT(t.transaction_id)), 2) AS avg_visit_spend
FROM `${PROJECT}.${DATASET}.fact_transaction` t
JOIN `${PROJECT}.${DATASET}.dim_member` m ON t.member_id = m.member_id
WHERE t.transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)
GROUP BY m.tier_name
ORDER BY avg_visit_spend DESC;
```

## 5. Chained / Follow-Up Variants
- The agent calls local tool `render_chart` with `chart_type='pie'` to create `outputs/uc2a_visit_spend_pie.png`.

## 6. Output Format & Visualization Specification
- **Visualization**: `pie`.
- File artifact written to: `outputs/uc2a_visit_spend_pie.png`.
- Must label slices with tier name, dollar value, and slice percentage.

## 7. Edge Cases, Pitfalls & Interpretation Notes
- While a pie chart typically represents shares of a whole, here it visually reflects the relative weighting of basket sizes across tiers as requested by the business stakeholder.

