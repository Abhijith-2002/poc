---
type: BigQuery Table
resource: bigquery://${PROJECT}/${DATASET}/fact_transaction_line
title: "Transaction Line Item Fact (fact_transaction_line)"
description: "Itemized line items and product categories purchased within a transaction."
tags:
  - bigquery
  - schema
  - fact_transaction_line
status: stable
generated:
  by: okf-schema-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/index.md"
---

# Transaction Line Item Fact (fact_transaction_line)

## Overview
Itemized line items and product categories purchased within a transaction.

- **Resource URI**: `bigquery://${PROJECT}/${DATASET}/fact_transaction_line`
- **Grain**: One row per product category line within a transaction.
- **Primary Key**: `line_id`
- **Partitioning**: None
- **Clustering**: CLUSTER BY transaction_id.

## Column Specifications
| Column | Data Type | Description | Values / Nullable |
|---|---|---|---|
| `line_id` | `STRING` | Primary key. Unique basket line item identifier. | Unique Line code |
| `transaction_id` | `STRING` | Foreign key to fact_transaction.transaction_id. | Foreign key |
| `product_category` | `STRING` | Merchandise category ('Apparel', 'Footwear', 'Beauty', 'Home', etc.). | Category |
| `quantity` | `INTEGER` | Quantity of units purchased in line. | >= 1 |
| `line_amount` | `NUMERIC` | Line-item subtotal monetary spend. | Currency (> 0.0) |


## Join Paths & Relationships
- `fact_transaction_line.transaction_id -> fact_transaction.transaction_id`

## Cost & Query Guidance
> [!IMPORTANT]
> Line item fact table (~1.6M rows). Join with fact_transaction when category breakdown is needed.

Related concepts:
- [Loyalty POC Dataset](/datasets/loyalty_poc/index.md)
- [vw_member_transactions View](/datasets/loyalty_poc/views/vw_member_transactions.md)
