---
type: Use Case
use_case_id: UC7
title: Rank top 100 members with staff_indicator = Y by high transaction frequency in the last month
description: Identifies internal staff members with the highest transaction frequency, highlighting days with multiple transactions on the same calendar day over the last month.
runtime: bigquery
parameters:
  - name: window_days
    type: integer
    default: 30
    required: true
    description: "Trailing observation window in calendar days (last month)."
  - name: top_n
    type: integer
    default: 100
    required: true
    description: "Number of staff members to return."
output_columns:
  - name: member_id
    type: string
  - name: first_name
    type: string
  - name: last_name
    type: string
  - name: total_transactions
    type: integer
  - name: distinct_active_days
    type: integer
  - name: multi_transaction_days
    type: integer
  - name: total_spend
    type: float
visualization: none
validation:
  min_rows: 10
  max_rows: 100
  assertions:
    - "total_transactions > 0"
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/dim_member.md"
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/glossary/staff-indicator.md"
  - "/glossary/visit.md"
---

# UC7: Top 100 Staff Members by Transaction Frequency (Last Month)

## 1. Intent & Example Questions
- "Rank top 100 members with staff_indicator = 'Y' (team members) by high transaction frequency, including days with multiple transactions per day, in the last month."
- "Show me employee accounts with the most transactions over the past 30 days and how many days had multiple purchases."
- "Top team members ranked by transaction activity and same-day multi-purchases in the last month."

## 2. Parameters & Defaults
- `@window_days` (INT64, default: `30`): Observation window relative to `CURRENT_DATE()`.
- `@top_n` (INT64, default: `100`): Maximum rows returned.

## 3. Business Rules & Definitions
- Filters strictly on `dim_member.staff_indicator = 'Y'`.
- Partitions `transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_days DAY)`.
- Metric calculations:
  - `total_transactions`: Total completed orders (`COUNT(transaction_id)`).
  - `distinct_active_days`: Distinct calendar dates transacted (`COUNT(DISTINCT transaction_date)`).
  - `multi_transaction_days`: Count of calendar dates on which the member completed **more than one** transaction (`COUNTIF(txns_in_day > 1)`).

## 4. Canonical BigQuery SQL Template
```sql
WITH staff_members AS (
  SELECT member_id, first_name, last_name
  FROM `${PROJECT}.${DATASET}.dim_member`
  WHERE staff_indicator = 'Y'
),
daily_txns AS (
  SELECT
    t.member_id,
    t.transaction_date,
    COUNT(t.transaction_id) AS txns_in_day,
    SUM(t.total_amount) AS daily_spend
  FROM `${PROJECT}.${DATASET}.fact_transaction` t
  JOIN staff_members s ON t.member_id = s.member_id
  WHERE t.transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_days DAY)
  GROUP BY t.member_id, t.transaction_date
),
staff_summary AS (
  SELECT
    member_id,
    SUM(txns_in_day) AS total_transactions,
    COUNT(transaction_date) AS distinct_active_days,
    COUNTIF(txns_in_day > 1) AS multi_transaction_days,
    ROUND(SUM(daily_spend), 2) AS total_spend
  FROM daily_txns
  GROUP BY member_id
)
SELECT
  s.member_id,
  m.first_name,
  m.last_name,
  s.total_transactions,
  s.distinct_active_days,
  s.multi_transaction_days,
  s.total_spend
FROM staff_summary s
JOIN staff_members m ON s.member_id = m.member_id
ORDER BY s.total_transactions DESC, s.multi_transaction_days DESC
LIMIT 100;
```

## 5. Chained / Follow-Up Variants
- None.

## 6. Output Format & Visualization Specification
- **Visualization**: `none` (tabular ranking).
- Staff names are masked unless `SHOW_PII=true`.

## 7. Edge Cases, Pitfalls & Interpretation Notes
- `COUNTIF(txns_in_day > 1)` cleanly computes the multi-transaction days without expensive self-joins.

