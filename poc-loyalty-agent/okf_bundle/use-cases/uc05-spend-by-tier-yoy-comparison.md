---
type: Use Case
use_case_id: UC5
title: Chart spend by member tier this year vs last year highlight green when up red when down
description: Compares Calendar Year-to-Date (YTD) member spend across tiers against the equivalent prior year period, highlighting positive and negative variances.
runtime: bigquery
parameters:
  - name: ytd_mode
    type: string
    default: "calendar_ytd"
    required: true
    description: "Year-to-date calculation mode matching same day of year."
output_columns:
  - name: tier_name
    type: string
  - name: last_year_spend
    type: float
  - name: this_year_spend
    type: float
  - name: delta_spend
    type: float
  - name: pct_change
    type: float
  - name: variance_indicator
    type: string
visualization: grouped_bar
validation:
  min_rows: 4
  max_rows: 4
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/datasets/loyalty_poc/tables/dim_member.md"
  - "/glossary/tier.md"
  - "/conventions/date-windows.md"
  - "/conventions/visualization-standards.md"
---

# UC5: Spend by Member Tier This Year vs Last Year

## 1. Intent & Example Questions
- "Chart spend by member tier this year vs last year; highlight green when up, red when down."
- "Show YoY tier spend comparison with green for increases and red for decreases."
- "Compare Calendar YTD spend by tier against last year same period with variance colors."

## 2. Parameters & Defaults
- Evaluates dynamically using [Date Windows Convention](/conventions/date-windows.md):
  - Current Year: `DATE_TRUNC(CURRENT_DATE(), YEAR)` through `CURRENT_DATE()`.
  - Prior Year: `DATE_SUB(DATE_TRUNC(CURRENT_DATE(), YEAR), INTERVAL 1 YEAR)` through `DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR)`.

## 3. Business Rules & Definitions
- Aggregates spend `SUM(t.total_amount)` by `dim_member.tier_name` for both periods.
- Calculates:
  $$\text{delta\_spend} = \text{this\_year\_spend} - \text{last\_year\_spend}$$
  $$\text{pct\_change} = \frac{\text{delta\_spend}}{\text{last\_year\_spend}} \times 100.0$$
- Highlights green if `delta_spend > 0`, red if `delta_spend < 0`.

## 4. Canonical BigQuery SQL Template
```sql
WITH current_period AS (
  SELECT
    m.tier_name,
    ROUND(SUM(t.total_amount), 2) AS this_year_spend
  FROM `${PROJECT}.${DATASET}.fact_transaction` t
  JOIN `${PROJECT}.${DATASET}.dim_member` m ON t.member_id = m.member_id
  WHERE t.transaction_date BETWEEN DATE_TRUNC(CURRENT_DATE(), YEAR) AND CURRENT_DATE()
  GROUP BY m.tier_name
),
prior_period AS (
  SELECT
    m.tier_name,
    ROUND(SUM(t.total_amount), 2) AS last_year_spend
  FROM `${PROJECT}.${DATASET}.fact_transaction` t
  JOIN `${PROJECT}.${DATASET}.dim_member` m ON t.member_id = m.member_id
  WHERE t.transaction_date BETWEEN DATE_SUB(DATE_TRUNC(CURRENT_DATE(), YEAR), INTERVAL 1 YEAR)
                              AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR)
  GROUP BY m.tier_name
)
SELECT
  c.tier_name,
  COALESCE(p.last_year_spend, 0.0) AS last_year_spend,
  c.this_year_spend,
  ROUND(c.this_year_spend - COALESCE(p.last_year_spend, 0.0), 2) AS delta_spend,
  ROUND(SAFE_DIVIDE(c.this_year_spend - COALESCE(p.last_year_spend, 0.0), p.last_year_spend) * 100.0, 2) AS pct_change,
  CASE
    WHEN c.this_year_spend >= COALESCE(p.last_year_spend, 0.0) THEN 'UP (Green)'
    ELSE 'DOWN (Red)'
  END AS variance_indicator
FROM current_period c
LEFT JOIN prior_period p ON c.tier_name = p.tier_name
ORDER BY c.this_year_spend DESC;
```

## 5. Chained / Follow-Up Variants
- The local tool `render_chart` is invoked with `chart_type='grouped_bar'` and `highlight_variance=True` to generate `outputs/uc5_yoy_tier_spend.png`.

## 6. Output Format & Visualization Specification
- **Visualization**: `grouped_bar`.
- Output path: `outputs/uc5_yoy_tier_spend.png`.
- Side-by-side bars for Last Year vs This Year per tier.
- **Color Rule**: Green when This Year > Last Year, Red when This Year < Last Year.
- Percentage variance label annotated on top of each bar cluster (e.g. `+15.2%` in green, `-12.5%` in red).

## 7. Edge Cases, Pitfalls & Interpretation Notes
- Comparing Calendar YTD ensures seasonality through the holiday period is not unfairly penalized when queried mid-year.

