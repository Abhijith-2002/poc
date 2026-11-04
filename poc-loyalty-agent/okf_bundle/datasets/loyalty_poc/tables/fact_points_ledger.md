---
type: BigQuery Table
resource: bigquery://${PROJECT}/${DATASET}/fact_points_ledger
title: "Points Ledger Fact (fact_points_ledger)"
description: "Historical audit ledger of loyalty points accrued, redeemed, expired, or adjusted."
tags:
  - bigquery
  - schema
  - fact_points_ledger
status: stable
generated:
  by: okf-schema-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/index.md"
---

# Points Ledger Fact (fact_points_ledger)

## Overview
Historical audit ledger of loyalty points accrued, redeemed, expired, or adjusted.

- **Resource URI**: `bigquery://${PROJECT}/${DATASET}/fact_points_ledger`
- **Grain**: One row per points balance mutation event.
- **Primary Key**: `ledger_id`
- **Partitioning**: PARTITION BY DATE(event_ts)
- **Clustering**: CLUSTER BY member_id.

## Column Specifications
| Column | Data Type | Description | Values / Nullable |
|---|---|---|---|
| `ledger_id` | `STRING` | Primary key. Unique points event identifier. | Unique PL code |
| `member_id` | `STRING` | Foreign key to dim_member.member_id. | Foreign key |
| `event_ts` | `TIMESTAMP` | Exact timestamp when points mutation occurred. | Timestamp |
| `event_type` | `STRING` | Mutation type ('EARN', 'REDEEM', 'EXPIRE', 'ADJUST'). | Category |
| `points` | `INTEGER` | Points value added or subtracted. | Integer (+/-) |
| `balance_after` | `INTEGER` | Cumulative member points balance immediately following event. | >= 0 |


## Join Paths & Relationships
- `fact_points_ledger.member_id -> dim_member.member_id`

## Cost & Query Guidance
> [!IMPORTANT]
> Audit table tracking points history (~375k rows).

Related concepts:
- [Loyalty POC Dataset](/datasets/loyalty_poc/index.md)
- [vw_member_transactions View](/datasets/loyalty_poc/views/vw_member_transactions.md)
