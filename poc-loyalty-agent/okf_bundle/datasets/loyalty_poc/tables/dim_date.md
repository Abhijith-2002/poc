---
type: BigQuery Table
resource: bigquery://${PROJECT}/${DATASET}/dim_date
title: "Date Dimension (dim_date)"
description: "Calendar dimension containing day, month, quarter, year, and holiday flags."
tags:
  - bigquery
  - schema
  - dim_date
status: stable
generated:
  by: okf-schema-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/index.md"
---

# Date Dimension (dim_date)

## Overview
Calendar dimension containing day, month, quarter, year, and holiday flags.

- **Resource URI**: `bigquery://${PROJECT}/${DATASET}/dim_date`
- **Grain**: One row per calendar date.
- **Primary Key**: `date_key`
- **Partitioning**: None
- **Clustering**: None

## Column Specifications
| Column | Data Type | Description | Values / Nullable |
|---|---|---|---|
| `date_key` | `INTEGER` | Surrogate integer key in YYYYMMDD format. | YYYYMMDD |
| `full_date` | `DATE` | Actual calendar date. | Date |
| `day_of_week` | `INTEGER` | Day of week (1=Monday .. 7=Sunday). | 1 to 7 |
| `day_name` | `STRING` | Day name (Monday, Tuesday, etc.). | Day name |
| `day_of_month` | `INTEGER` | Day of month (1 to 31). | 1 to 31 |
| `month_num` | `INTEGER` | Month number (1 to 12). | 1 to 12 |
| `month_name` | `STRING` | Month name (January, February, etc.). | Month name |
| `quarter` | `INTEGER` | Calendar quarter (1 to 4). | 1 to 4 |
| `year` | `INTEGER` | Calendar year (e.g. 2025, 2026). | Year |
| `is_weekend` | `BOOLEAN` | TRUE if Saturday or Sunday. | TRUE / FALSE |
| `is_holiday` | `BOOLEAN` | TRUE if major public holiday. | TRUE / FALSE |


## Join Paths & Relationships
- `dim_date.full_date -> fact_transaction.transaction_date`

## Cost & Query Guidance
> [!IMPORTANT]
> Calendar lookup table (1,826 rows).

Related concepts:
- [Loyalty POC Dataset](/datasets/loyalty_poc/index.md)
- [vw_member_transactions View](/datasets/loyalty_poc/views/vw_member_transactions.md)
