---
type: Use Case
use_case_id: UC8
title: Number of members in Gold tier with points threshold who have not transacted in past 2 months
description: Counts inactive Gold tier loyalty members holding significant point balances who have not transacted in the past 2 months.
runtime: bigquery
parameters:
  - name: points_threshold
    type: integer
    default: null
    required: true
    description: "Minimum points balance threshold (xx). Mandatory runtime parameter; ask the user if omitted."
  - name: window_months
    type: integer
    default: 2
    required: true
    description: "Inactivity observation window in months."
output_columns:
  - name: points_threshold
    type: integer
  - name: inactivity_window_months
    type: integer
  - name: inactive_gold_member_count
    type: integer
visualization: none
validation:
  min_rows: 1
  max_rows: 1
  assertions:
    - "inactive_gold_member_count >= 0"
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/dim_member.md"
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/glossary/tier.md"
  - "/glossary/active-inactive-member.md"
---

# UC8: Count of Inactive Gold Members with High Points

## 1. Intent & Example Questions
- "How many members in Gold tier with points >= 3000 haven't transacted in the past 2 months?"
- "Number of members in Gold tier with points >= {xx} who haven't transacted in the past 2 months."
- "Count Gold customers with at least 5000 points who are dormant for 2 months."

## 2. Parameters & Defaults
- `@points_threshold` (INT64, REQUIRED): Point balance cutoff.
  > [!IMPORTANT]
  > This is a mandatory parameter. If the user does not specify a threshold in their query, the agent must pause and ask the user for the desired points cutoff value before executing.
- `@window_months` (INT64, default: `2`): Trailing inactivity window (`DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)`).

## 3. Business Rules & Definitions
- Restricts members to `dim_member.tier_name = 'Gold'`.
- Filters members where `points_balance >= @points_threshold`.
- Inactivity: Member must NOT appear in `fact_transaction` with `transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)`.
- Output is a single count metric.

## 4. Canonical BigQuery SQL Template
```sql
WITH recent_transactors AS (
  SELECT DISTINCT member_id
  FROM `${PROJECT}.${DATASET}.fact_transaction`
  WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)
)
SELECT
  @points_threshold AS points_threshold,
  @window_months AS inactivity_window_months,
  COUNT(m.member_id) AS inactive_gold_member_count
FROM `${PROJECT}.${DATASET}.dim_member` m
LEFT JOIN recent_transactors t ON m.member_id = t.member_id
WHERE m.tier_name = 'Gold'
  AND m.points_balance >= @points_threshold
  AND t.member_id IS NULL;
```

## 5. Chained / Follow-Up Variants
- None.

## 6. Output Format & Visualization Specification
- **Visualization**: `none` (single row scalar summary count).

## 7. Edge Cases, Pitfalls & Interpretation Notes
- If `@points_threshold` is missing from user input, DO NOT guess or assume a default; ask: "What points threshold would you like to use for Gold members (e.g. 1000, 3000, 5000)?"

