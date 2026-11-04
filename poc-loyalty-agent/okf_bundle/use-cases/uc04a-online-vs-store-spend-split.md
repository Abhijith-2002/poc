---
type: Use Case
use_case_id: UC4a
parent_use_case: "use-cases/uc04-new-joiners-high-frequency-spend"
title: Break-up of Online vs In-Store Spend for Top 100 New Joiners
description: Shows the division between e-commerce and brick-and-mortar retail spend for the top 100 high-frequency new joiners identified in UC4.
runtime: bigquery
inputs_from_parent:
  - member_id
  - first_name
  - last_name
  - total_spend
  - visit_count
parameters:
  - name: join_window_months
    type: integer
    default: 6
    required: true
    description: "Join window inherited from UC4."
  - name: min_visits
    type: integer
    default: 5
    required: true
    description: "Visit threshold inherited from UC4."
  - name: top_n
    type: integer
    default: 100
    required: true
    description: "Row count inherited from UC4."
output_columns:
  - name: member_id
    type: string
  - name: first_name
    type: string
  - name: last_name
    type: string
  - name: total_spend
    type: float
  - name: store_spend
    type: float
  - name: online_spend
    type: float
  - name: online_spend_pct
    type: float
visualization: none
validation:
  min_rows: 50
  max_rows: 100
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/use-cases/uc04-new-joiners-high-frequency-spend.md"
  - "/glossary/channel-in-store-vs-online.md"
  - "/metrics/online-spend-share.md"
---

# UC4a: Online vs In-Store Spend Split for Top 100 New Joiners

## 1. Intent & Example Questions
- "Of those 100, show the break-up of online vs in-store spend."
- "Break down their spend between digital and retail stores."
- "For those top new joiners, how much was spent online versus in physical stores?"

## 2. Parameters & Defaults
- Reuses all filters and parameters from parent [UC4](/use-cases/uc04-new-joiners-high-frequency-spend.md):
  - `@join_window_months` (default: `6`)
  - `@min_visits` (default: `5`)
  - `@top_n` (default: `100`)

## 3. Business Rules & Definitions
- Isolates the exact top 100 member cohort determined in UC4.
- Sums `total_amount` where `channel = 'STORE'` and `channel = 'ONLINE'`.
- Calculates `online_spend_pct = (online_spend / total_spend) * 100.0`.

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
),
top_100_cohort AS (
  SELECT
    r.member_id,
    r.first_name,
    r.last_name,
    a.total_spend
  FROM member_activity a
  JOIN recent_joiners r ON a.member_id = r.member_id
  ORDER BY a.total_spend DESC
  LIMIT 100
),
channel_spend AS (
  SELECT
    t.member_id,
    ROUND(SUM(CASE WHEN t.channel = 'STORE' THEN t.total_amount ELSE 0 END), 2) AS store_spend,
    ROUND(SUM(CASE WHEN t.channel = 'ONLINE' THEN t.total_amount ELSE 0 END), 2) AS online_spend
  FROM `${PROJECT}.${DATASET}.fact_transaction` t
  JOIN top_100_cohort c ON t.member_id = c.member_id
  WHERE t.transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @join_window_months MONTH)
  GROUP BY t.member_id
)
SELECT
  c.member_id,
  c.first_name,
  c.last_name,
  c.total_spend,
  COALESCE(cs.store_spend, 0.0) AS store_spend,
  COALESCE(cs.online_spend, 0.0) AS online_spend,
  ROUND(SAFE_DIVIDE(cs.online_spend, c.total_spend) * 100.0, 2) AS online_spend_pct
FROM top_100_cohort c
LEFT JOIN channel_spend cs ON c.member_id = cs.member_id
ORDER BY c.total_spend DESC;
```

## 5. Chained / Follow-Up Variants
- The agent can reuse the parent's cached cohort from virtual memory or re-execute the canonical query above.

## 6. Output Format & Visualization Specification
- **Visualization**: `none` (tabular breakdown + cohort aggregate summary).
- Names masked unless `SHOW_PII=true`.

## 7. Edge Cases, Pitfalls & Interpretation Notes
- Some members may have 100% store spend or 100% online spend; `COALESCE` guarantees non-null numbers.

