---
type: BigQuery Table
resource: bigquery://${PROJECT}/${DATASET}/fact_transaction
title: "Transaction Fact (fact_transaction)"
description: "Sales transactions recorded across retail stores and digital e-commerce channels."
tags:
  - bigquery
  - schema
  - fact_transaction
status: stable
generated:
  by: okf-schema-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/index.md"
---

# Transaction Fact (fact_transaction)

## Overview
Sales transactions recorded across retail stores and digital e-commerce channels.

- **Resource URI**: `bigquery://${PROJECT}/${DATASET}/fact_transaction`
- **Grain**: One row per sales transaction order.
- **Primary Key**: `transaction_id`
- **Partitioning**: PARTITION BY transaction_date (DAILY). Partition pruning is mandatory.
- **Clustering**: CLUSTER BY member_id, store_id.

## Column Specifications
| Column | Data Type | Description | Values / Nullable |
|---|---|---|---|
| `transaction_id` | `STRING` | Primary key. Unique transaction order identifier. | Unique TXN code |
| `member_id` | `STRING` | Foreign key to dim_member.member_id. | Foreign key |
| `store_id` | `STRING` | Foreign key to dim_store.store_id (e.g. 'S01' Doncaster, 'S16' ONLINE). | Foreign key |
| `channel` | `STRING` | Channel used: 'STORE' or 'ONLINE'. | 'STORE', 'ONLINE' |
| `transaction_ts` | `TIMESTAMP` | Exact timestamp when transaction completed. | Timestamp (UTC) |
| `transaction_date` | `DATE` | Partitioning key. Calendar date of transaction. | Date |
| `total_amount` | `NUMERIC` | Final monetary amount paid (net of discounts). | Currency (> 0.0) |
| `discount_amount` | `NUMERIC` | Total promotional or staff discount applied. | Currency (>= 0.0) |
| `items_count` | `INTEGER` | Number of distinct items/units in basket. | >= 1 |
| `points_earned` | `INTEGER` | Loyalty points awarded on this transaction. | >= 0 |
| `payment_type` | `STRING` | Tender method (CREDIT_CARD, APPLE_PAY, AFTERPAY, etc.). | Payment category |


## Join Paths & Relationships
- `fact_transaction.member_id -> dim_member.member_id`
- `fact_transaction.store_id -> dim_store.store_id`
- `fact_transaction.transaction_date -> dim_date.full_date`
- `fact_transaction.transaction_id -> fact_transaction_line.transaction_id`

## Cost & Query Guidance
> [!IMPORTANT]
> Core fact table (~1.5M rows). ALWAYS filter queries on transaction_date to avoid full partition scans.

Related concepts:
- [Loyalty POC Dataset](/datasets/loyalty_poc/index.md)
- [vw_member_transactions View](/datasets/loyalty_poc/views/vw_member_transactions.md)
