---
type: BigQuery View
resource: bigquery://${PROJECT}/${DATASET}/vw_member_transactions
title: "Denormalized Member Transactions View (vw_member_transactions)"
description: "Pre-joined view joining transactions with member demographics, tier attributes, and store locations."
tags:
  - bigquery
  - view
  - vw_member_transactions
status: stable
generated:
  by: okf-schema-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/datasets/loyalty_poc/tables/dim_member.md"
  - "/datasets/loyalty_poc/tables/dim_store.md"
---

# Denormalized Member Transactions View (`vw_member_transactions`)

## Overview
`vw_member_transactions` flattens transactions with member demographics and store attributes, providing an optimized, easy-to-query dataset for analytical use cases.

## Underlying SQL Definition
```sql
SELECT
  t.transaction_id,
  t.member_id,
  t.store_id,
  t.channel,
  t.transaction_ts,
  t.transaction_date,
  t.total_amount,
  t.discount_amount,
  t.items_count,
  t.points_earned,
  t.payment_type,
  m.first_name,
  m.last_name,
  m.email,
  m.contactable_by_email,
  m.age,
  m.age_band,
  m.gender,
  m.state AS member_state,
  m.join_date,
  m.tier_id,
  m.tier_name,
  m.staff_indicator,
  s.store_name,
  s.state AS store_state,
  s.channel_type
FROM `${PROJECT}.${DATASET}.fact_transaction` t
LEFT JOIN `${PROJECT}.${DATASET}.dim_member` m ON t.member_id = m.member_id
LEFT JOIN `${PROJECT}.${DATASET}.dim_store` s ON t.store_id = s.store_id
```

## Key Grain & Cost Guidance
- **Grain**: One row per sales transaction.
- **Partition Filtering**: Filters on `transaction_date` are pushed directly down to `fact_transaction`, maintaining optimal partition pruning and lowest query cost.
