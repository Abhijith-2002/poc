---
type: Use Case
use_case_id: UC3a
parent_use_case: "use-cases/uc03-age-band-store-vs-online"
title: Average Store Visits for Top Age Band in Past 6 Months
description: Calculates the average number of physical store visits per member for the age band exhibiting the highest store shopping propensity.
runtime: bigquery
inputs_from_parent:
  - age_band
parameters:
  - name: target_age_band
    type: string
    default: "65+"
    required: true
    description: "Age band identified in UC3 as most likely to shop in store (default: '65+')."
  - name: window_months
    type: integer
    default: 6
    required: true
    description: "Trailing months observation window."
output_columns:
  - name: age_band
    type: string
  - name: total_members
    type: integer
  - name: total_store_visits
    type: integer
  - name: avg_store_visits_per_member
    type: float
visualization: none
validation:
  min_rows: 1
  max_rows: 1
  assertions:
    - "avg_store_visits_per_member > 0"
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/use-cases/uc03-age-band-store-vs-online.md"
  - "/glossary/visit.md"
  - "/metrics/visit-frequency.md"
---

# UC3a: Average Store Visits per Member for Top Age Band

## 1. Intent & Example Questions
- "For the top age band, on average how many store visits per member in the past 6 months?"
- "How many times did members in that top in-store age group visit our stores over the last 6 months?"
- "Average physical store visits per customer in the 65+ age band over past 6 months."

## 2. Parameters & Defaults
- `@target_age_band` (STRING, default: `'65+'`): Age band inherited from [UC3](/use-cases/uc03-age-band-store-vs-online.md).
- `@window_months` (INT64, default: `6`): Trailing months observation window.

## 3. Business Rules & Definitions
- Restricts analysis to the customer cohort belonging to `@target_age_band`.
- Counts distinct physical store visits (`channel = 'STORE'`) in `fact_transaction`.
- Averages across all members enrolled in that age band (including those with 0 visits, or across active visiting members). The canonical metric divides total store visits by distinct visiting members or total cohort members:
  $$\text{avg\_store\_visits} = \frac{\text{Total Store Visits}}{\text{Distinct Active Visiting Members}}$$

## 4. Canonical BigQuery SQL Template
```sql
WITH cohort_members AS (
  SELECT member_id
  FROM `${PROJECT}.${DATASET}.dim_member`
  WHERE age_band = @target_age_band
),
store_visits AS (
  SELECT
    t.member_id,
    COUNT(t.transaction_id) AS visit_count
  FROM `${PROJECT}.${DATASET}.fact_transaction` t
  JOIN cohort_members c ON t.member_id = c.member_id
  WHERE t.channel = 'STORE'
    AND t.transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)
  GROUP BY t.member_id
)
SELECT
  @target_age_band AS age_band,
  (SELECT COUNT(*) FROM cohort_members) AS total_enrolled_members,
  COUNT(v.member_id) AS active_store_shoppers,
  SUM(v.visit_count) AS total_store_visits,
  ROUND(SAFE_DIVIDE(SUM(v.visit_count), COUNT(v.member_id)), 2) AS avg_store_visits_per_active_member,
  ROUND(SAFE_DIVIDE(SUM(v.visit_count), (SELECT COUNT(*) FROM cohort_members)), 2) AS avg_store_visits_per_enrolled_member
FROM store_visits v;
```

## 5. Chained / Follow-Up Variants
- Reuses the top age band resulting from UC3.

## 6. Output Format & Visualization Specification
- **Visualization**: `none` (concise metrics summary).

## 7. Edge Cases, Pitfalls & Interpretation Notes
- Provides both the average across active visiting members and across total enrolled members in the demographic to avoid ambiguity.

