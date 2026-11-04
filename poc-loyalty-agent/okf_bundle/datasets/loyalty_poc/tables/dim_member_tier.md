---
type: BigQuery Table
resource: bigquery://${PROJECT}/${DATASET}/dim_member_tier
title: "Loyalty Tier Dimension (dim_member_tier)"
description: "Loyalty tiers, spend qualification thresholds, and points accrual multipliers."
tags:
  - bigquery
  - schema
  - dim_member_tier
status: stable
generated:
  by: okf-schema-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/index.md"
---

# Loyalty Tier Dimension (dim_member_tier)

## Overview
Loyalty tiers, spend qualification thresholds, and points accrual multipliers.

- **Resource URI**: `bigquery://${PROJECT}/${DATASET}/dim_member_tier`
- **Grain**: One row per loyalty tier level.
- **Primary Key**: `tier_id`
- **Partitioning**: None
- **Clustering**: None

## Column Specifications
| Column | Data Type | Description | Values / Nullable |
|---|---|---|---|
| `tier_id` | `INTEGER` | Primary key (1: Bronze, 2: Silver, 3: Gold, 4: Platinum). | 1, 2, 3, 4 |
| `tier_name` | `STRING` | Tier level name. | 'Bronze', 'Silver', 'Gold', 'Platinum' |
| `threshold_spend` | `NUMERIC` | Annual spend threshold to achieve or retain tier. | >= 0.0 |
| `points_multiplier` | `NUMERIC` | Points earned per dollar spent. | 1.0 to 2.0 |
| `benefits` | `STRING` | Summary of tier perks (shipping, VIP events, gifts). | Text |


## Join Paths & Relationships
- `dim_member_tier.tier_id -> dim_member.tier_id`

## Cost & Query Guidance
> [!IMPORTANT]
> Static reference lookup table (4 rows). Negligible scan cost.

Related concepts:
- [Loyalty POC Dataset](/datasets/loyalty_poc/index.md)
- [vw_member_transactions View](/datasets/loyalty_poc/views/vw_member_transactions.md)
