---
type: Use Case
use_case_id: UC4
title: Top 100 members who joined in the last 6 months with high visit frequency ranked by member spend
description: Ranks newly enrolled loyalty members who exhibit frequent shopping visits by their total spend.
runtime: bigquery
parameters:
  - name: join_window_months
    type: integer
    default: 6
    required: true
    description: "Months since enrollment."
  - name: min_visits
    type: integer
    default: 5
    required: true
    description: "Minimum visit threshold defining high frequency."
  - name: top_n
    type: integer
    default: 100
    required: true
    description: "Number of top ranking members."
output_columns:
  - name: member_id
    type: string
  - name: first_name
    type: string
  - name: last_name
    type: string
  - name: join_date
    type: date
  - name: tier_name
    type: string
  - name: visit_count
    type: integer
  - name: total_spend
    type: float
visualization: none
validation:
  min_rows: 50
  max_rows: 100
  assertions:
    - "total_spend > 0"
    - "visit_count >= 5"
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/dim_member.md"
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/glossary/high-frequency.md"
  - "/glossary/member-spend.md"
---

# UC4: Top 100 New Joiners with High Visit Frequency Ranked by Spend

## 1. Intent & Example Questions
- "Top 100 members who joined in the last 6 months with high visit frequency, ranked by member spend."
- "Show me our best new customers: joined in past 6 months, high visit count, ranked by spend."
- "Who are the highest-spending recent joiners who shop frequently?"

## 2. Parameters & Defaults
- `@join_window_months` (INT64, default: `6`): `join_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @join_window_months MONTH)`.
- `@min_visits` (INT64, default: `5`): Minimum transaction threshold defining [High Frequency](/glossary/high-frequency.md).
- `@top_n` (INT64, default: `100`): Maximum rows returned.

## 3. Business Rules & Definitions
- Customer must have joined within the last 6 months (`join_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)`).
- Visits evaluated as distinct transactions in `fact_transaction` within the last 6 months.
- Ranked by `total_spend DESC`.

## 4. Canonical BigQuery SQL Template
```sql
WITH recent_joiners AS (
  SELECT
    member_id,
    first_name,
    last_name,
    join_date,
    tier_name
  FROM `${PROJECT}.${DATASET}.dim_member`
  WHERE join_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @join_window_months MONTH)
),
member_activity AS (
  SELECT
    t.member_id,
    COUNT(t.transaction_id) AS visit_count,
    ROUND(SUM(t.total_amount), 2) AS total_spend
  FROM `${PROJECT}.${DATASET}.fact_transaction` t
  JOIN recent_joiners r ON t.member_id = r.member_id
  WHERE t.transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @join_window_months MONTH)
  GROUP BY t.member_id
  HAVING COUNT(t.transaction_id) >= @min_visits
)
SELECT
  r.member_id,
  r.first_name,
  r.last_name,
  r.join_date,
  r.tier_name,
  a.visit_count,
  a.total_spend
FROM member_activity a
JOIN recent_joiners r ON a.member_id = r.member_id
ORDER BY a.total_spend DESC
LIMIT 100;
```

## 5. Chained / Follow-Up Variants
- Followed by [UC4a: Online vs Store Spend Split](/use-cases/uc04a-online-vs-store-spend-split.md) which breaks down online vs physical store spend for these 100 members.

## 6. Output Format & Visualization Specification
- **Visualization**: `none` (tabular summary).
- Names are masked unless `SHOW_PII=true`.

## 7. Edge Cases, Pitfalls & Interpretation Notes
- `transaction_date` filter must be applied to `fact_transaction` to enable BigQuery partition pruning.

