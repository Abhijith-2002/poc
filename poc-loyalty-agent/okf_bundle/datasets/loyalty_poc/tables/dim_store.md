---
type: BigQuery Table
resource: bigquery://${PROJECT}/${DATASET}/dim_store
title: "Store Dimension (dim_store)"
description: "Retail brick-and-mortar stores and digital pseudo-store locations."
tags:
  - bigquery
  - schema
  - dim_store
status: stable
generated:
  by: okf-schema-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/index.md"
---

# Store Dimension (dim_store)

## Overview
Retail brick-and-mortar stores and digital pseudo-store locations.

- **Resource URI**: `bigquery://${PROJECT}/${DATASET}/dim_store`
- **Grain**: One row per physical or digital retail storefront.
- **Primary Key**: `store_id`
- **Partitioning**: None
- **Clustering**: None

## Column Specifications
| Column | Data Type | Description | Values / Nullable |
|---|---|---|---|
| `store_id` | `STRING` | Primary key. Store identifier (e.g. S01, S02, S16). | Unique store code |
| `store_name` | `STRING` | Store name (e.g. 'Doncaster', 'Chadstone', 'ONLINE'). | Location name |
| `state` | `STRING` | State jurisdiction or 'National' for online. | 'VIC', 'NSW', 'QLD', etc. |
| `region` | `STRING` | Geographical sales region (e.g. 'Metro East', 'Digital'). | Region category |
| `channel_type` | `STRING` | Channel classification: 'STORE' or 'ONLINE'. | 'STORE', 'ONLINE' |


## Join Paths & Relationships
- `dim_store.store_id -> fact_transaction.store_id`

## Cost & Query Guidance
> [!IMPORTANT]
> Small reference table (16 rows).

Related concepts:
- [Loyalty POC Dataset](/datasets/loyalty_poc/index.md)
- [vw_member_transactions View](/datasets/loyalty_poc/views/vw_member_transactions.md)
