---
type: Use Case
use_case_id: UC1
title: Top 100 members by spend in the last 12 months at the Doncaster store who are contactable by email
description: Identifies the highest-spending loyalty members at Doncaster over the trailing 12 months with valid email opt-in.
runtime: bigquery
parameters:
  - name: store_name
    type: string
    default: "Doncaster"
    required: true
    description: "Name of the retail store location."
  - name: window_months
    type: integer
    default: 12
    required: true
    description: "Trailing observation window in calendar months."
  - name: top_n
    type: integer
    default: 100
    required: true
    description: "Number of top ranking members to return."
output_columns:
  - name: member_id
    type: string
  - name: first_name
    type: string
  - name: last_name
    type: string
  - name: email
    type: string
  - name: total_spend
    type: float
  - name: purchase_count
    type: integer
visualization: none
validation:
  min_rows: 100
  max_rows: 100
  assertions:
    - "total_spend > 0"
    - "purchase_count > 0"
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/datasets/loyalty_poc/tables/dim_member.md"
  - "/datasets/loyalty_poc/tables/dim_store.md"
  - "/glossary/contactable.md"
  - "/glossary/member-spend.md"
---

# UC1: Top 100 Members by Spend at Doncaster Contactable by Email

## 1. Intent & Example Questions
- "Who are the top 100 members by spend in the last 12 months at the Doncaster store who are contactable by email?"
- "Show me our highest spending loyalty customers at Doncaster over the past year who we can email for a VIP campaign."
- "Get top 100 email-contactable customers at Doncaster ranked by 12-month spend."

## 2. Parameters & Defaults
- `@store_name` (STRING, default: `'Doncaster'`): Filter matching `dim_store.store_name`.
- `@window_months` (INT64, default: `12`): Trailing date window relative to `CURRENT_DATE()`.
- `@top_n` (INT64, default: `100`): Maximum rows returned.

## 3. Business Rules & Definitions
- **Store Filter**: Must restrict transactions to the physical Doncaster store (`dim_store.store_name = 'Doncaster'`).
- **Contactability**: Requires [Contactable Member](/glossary/contactable.md) where `contactable_by_email = TRUE`.
- **Date Partition**: Filters `transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)`.
- **Spend Aggregation**: [Member Spend](/glossary/member-spend.md) calculated as `SUM(total_amount)`.
- **Purchases**: [Purchase Count](/metrics/purchase-count.md) counted as `COUNT(DISTINCT transaction_id)`.

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
)
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
LIMIT 100;
```

## 5. Chained / Follow-Up Variants
- Follow-up query [UC1a: Rank by Purchases](/use-cases/uc01a-rank-by-purchases.md) takes the 100 members identified by this query and sorts them by `purchase_count DESC`.

## 6. Output Format & Visualization Specification
- **Visualization**: `none` (tabular report).
- **PII Governance**: Member names and emails must be masked in conversational responses (e.g. `j***@d***.com`) per [PII Masking Conventions](/conventions/pii-masking.md) unless `SHOW_PII=true`.

## 7. Edge Cases, Pitfalls & Interpretation Notes
- Ensure `transaction_date` filter is placed directly in the `WHERE` clause of `fact_transaction` to trigger BigQuery partition pruning.
- Do not filter on `dim_member.status = 'ACTIVE'` unless requested; opt-in email contactability is the primary gating criterion.

