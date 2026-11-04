---
type: Use Case
use_case_id: UC1a
parent_use_case: "use-cases/uc01-top-members-doncaster-email"
title: Rank Top 100 Doncaster Spenders by Number of Purchases
description: Re-ranks the top 100 Doncaster email-contactable members from UC1 by their total number of purchases.
runtime: bigquery
inputs_from_parent:
  - member_id
  - first_name
  - last_name
  - email
  - total_spend
  - purchase_count
parameters:
  - name: store_name
    type: string
    default: "Doncaster"
    required: true
    description: "Store name inherited from UC1."
  - name: window_months
    type: integer
    default: 12
    required: true
    description: "Observation window inherited from UC1."
  - name: top_n
    type: integer
    default: 100
    required: true
    description: "Number of rows returned."
output_columns:
  - name: member_id
    type: string
  - name: first_name
    type: string
  - name: last_name
    type: string
  - name: email
    type: string
  - name: purchase_count
    type: integer
  - name: total_spend
    type: float
visualization: none
validation:
  min_rows: 100
  max_rows: 100
  assertions:
    - "purchase_count > 0"
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/use-cases/uc01-top-members-doncaster-email.md"
  - "/glossary/purchase.md"
  - "/metrics/purchase-count.md"
---

# UC1a: Rank Doncaster Spenders by Number of Purchases

## 1. Intent & Example Questions
- "Of those 100, rank by number of purchases."
- "Rank the top 100 Doncaster members by their purchase count instead of spend."
- "Show me which of those 100 members bought the most frequently."

## 2. Parameters & Defaults
- Reuses all parameters from parent [UC1](/use-cases/uc01-top-members-doncaster-email.md):
  - `@store_name` (default: `'Doncaster'`)
  - `@window_months` (default: `12`)
  - `@top_n` (default: `100`)

## 3. Business Rules & Definitions
- Re-orders the exact cohort of 100 members selected in UC1.
- Orders primarily by `purchase_count DESC`, tie-broken by `total_spend DESC`.
- See [Purchase Definition](/glossary/purchase.md) and [Purchase Count Metric](/metrics/purchase-count.md).

## 4. Canonical BigQuery SQL Template
```sql
WITH doncaster_store AS (
  SELECT store_id
  FROM `${PROJECT}.${DATASET}.dim_store`
  WHERE store_name = @store_name
),
recent_transactions AS (
  SELECT
    t.member_id,
    ROUND(SUM(t.total_amount), 2) AS total_spend,
    COUNT(DISTINCT t.transaction_id) AS purchase_count
  FROM `${PROJECT}.${DATASET}.fact_transaction` t
  JOIN doncaster_store s ON t.store_id = s.store_id
  WHERE t.transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)
  GROUP BY t.member_id
),
top_100_spenders AS (
  SELECT
    m.member_id,
    m.first_name,
    m.last_name,
    m.email,
    r.total_spend,
    r.purchase_count
  FROM recent_transactions r
  JOIN `${PROJECT}.${DATASET}.dim_member` m ON r.member_id = m.member_id
  WHERE m.contactable_by_email = TRUE
  ORDER BY r.total_spend DESC
  LIMIT 100
)
SELECT
  member_id,
  first_name,
  last_name,
  email,
  purchase_count,
  total_spend
FROM top_100_spenders
ORDER BY purchase_count DESC, total_spend DESC;
```

## 5. Chained / Follow-Up Variants
- If parent execution results are cached in the virtual filesystem (`/tmp/loyalty_state/last_execution.json`), the agent may re-sort the in-memory dataframe or re-execute the canonical query CTE above.

## 6. Output Format & Visualization Specification
- **Visualization**: `none` (tabular format).
- PII masking applies to `email` and customer names.

## 7. Edge Cases, Pitfalls & Interpretation Notes
- Note that re-ranking occurs *within* the top 100 spenders, rather than selecting the top 100 overall transactors from Doncaster.

