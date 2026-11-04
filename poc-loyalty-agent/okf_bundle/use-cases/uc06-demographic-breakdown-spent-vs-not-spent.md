---
type: Use Case
use_case_id: UC6
title: Demographic breakdown of members who have NOT spent in the last 6 months vs those who have
description: Compares customer demographic distributions (age band, gender, state, tier) between active spenders and dormant members over the past 6 months.
runtime: bigquery
parameters:
  - name: window_months
    type: integer
    default: 6
    required: true
    description: "Trailing months activity window."
output_columns:
  - name: activity_status
    type: string
  - name: age_band
    type: string
  - name: gender
    type: string
  - name: state
    type: string
  - name: tier_name
    type: string
  - name: member_count
    type: integer
visualization: none
validation:
  min_rows: 10
  assertions:
    - "member_count > 0"
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/dim_member.md"
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/glossary/active-inactive-member.md"
  - "/glossary/age-band.md"
---

# UC6: Demographic Breakdown of Dormant vs Active Members

## 1. Intent & Example Questions
- "Demographic breakdown of members who have NOT spent in the last 6 months vs those who have."
- "Compare active shoppers vs lapsed members over the last 6 months by age, gender, state, and tier."
- "Who are our dormant members who stopped spending in the last 6 months compared to active ones?"

## 2. Parameters & Defaults
- `@window_months` (INT64, default: `6`): Trailing months activity threshold.

## 3. Business Rules & Definitions
- Active: Member recorded at least one purchase in `fact_transaction` where `transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)`.
- Dormant / Not Spent: Member has 0 purchases in that window.
- Demographic dimensions: `age_band`, `gender`, `state`, `tier_name`.

## 4. Canonical BigQuery SQL Template
```sql
WITH recent_active_members AS (
  SELECT DISTINCT member_id
  FROM `${PROJECT}.${DATASET}.fact_transaction`
  WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)
),
member_classification AS (
  SELECT
    m.member_id,
    m.age_band,
    m.gender,
    m.state,
    m.tier_name,
    CASE
      WHEN a.member_id IS NOT NULL THEN 'Spent in Last 6 Months'
      ELSE 'NOT Spent in Last 6 Months'
    END AS activity_status
  FROM `${PROJECT}.${DATASET}.dim_member` m
  LEFT JOIN recent_active_members a ON m.member_id = a.member_id
)
SELECT
  activity_status,
  age_band,
  gender,
  state,
  tier_name,
  COUNT(member_id) AS member_count
FROM member_classification
GROUP BY activity_status, age_band, gender, state, tier_name
ORDER BY activity_status, member_count DESC;
```

## 5. Chained / Follow-Up Variants
- Can be filtered to specific demographic cuts (e.g. state or tier only) upon user request.

## 6. Output Format & Visualization Specification
- **Visualization**: `none` (tabular summary table with high-level totals of active vs dormant members).

## 7. Edge Cases, Pitfalls & Interpretation Notes
- Uses a distinct member lookup CTE with partition filtering rather than a raw outer join to optimize BigQuery scan performance.

