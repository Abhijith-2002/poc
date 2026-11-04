---
type: BigQuery Table
resource: bigquery://${PROJECT}/${DATASET}/dim_member
title: "Member Dimension (dim_member)"
description: "Retail loyalty programme customer profiles, contactability flags, demographics, and membership tier."
tags:
  - bigquery
  - schema
  - dim_member
status: stable
generated:
  by: okf-schema-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/index.md"
---

# Member Dimension (dim_member)

## Overview
Retail loyalty programme customer profiles, contactability flags, demographics, and membership tier.

- **Resource URI**: `bigquery://${PROJECT}/${DATASET}/dim_member`
- **Grain**: One row per enrolled loyalty member.
- **Primary Key**: `member_id`
- **Partitioning**: None
- **Clustering**: None

## Column Specifications
| Column | Data Type | Description | Values / Nullable |
|---|---|---|---|
| `member_id` | `STRING` | Primary key. Unique member identifier (e.g. M000001). | Required |
| `first_name` | `STRING` | Member given name. Classified as PII. | Required |
| `last_name` | `STRING` | Member surname. Classified as PII. | Required |
| `email` | `STRING` | Email address. Classified as PII. | Optional/Nullable |
| `email_opt_in` | `BOOLEAN` | Explicit consent to receive marketing emails. | TRUE / FALSE |
| `sms_opt_in` | `BOOLEAN` | Explicit consent to receive SMS marketing messages. | TRUE / FALSE |
| `contactable_by_email` | `BOOLEAN` | Precomputed flag: email present AND email_opt_in = TRUE. | TRUE / FALSE |
| `date_of_birth` | `DATE` | Member date of birth (YYYY-MM-DD). | Historical date |
| `age` | `INTEGER` | Calculated member age in years. | 18 to 90 |
| `age_band` | `STRING` | Standard age band: '18-24', '25-34', '35-44', '45-54', '55-64', '65+'. | Standard bands |
| `gender` | `STRING` | Member gender: 'F', 'M', 'Other'. | Category |
| `state` | `STRING` | Australian state of residence ('VIC', 'NSW', 'QLD', etc.). | Category |
| `postcode` | `STRING` | Australian 4-digit residential postcode. | Numeric string |
| `join_date` | `DATE` | Date member enrolled in the loyalty programme. | Historical date |
| `tier_id` | `INTEGER` | Foreign key to dim_member_tier.tier_id (1: Bronze, 2: Silver, 3: Gold, 4: Platinum). | 1 to 4 |
| `tier_name` | `STRING` | Denormalized loyalty tier name. | Bronze, Silver, Gold, Platinum |
| `points_balance` | `INTEGER` | Current accrued loyalty points balance. | >= 0 |
| `staff_indicator` | `STRING` | 'Y' if employee/staff member, 'N' if regular customer. | 'Y' or 'N' |
| `status` | `STRING` | Account status: 'ACTIVE' or 'INACTIVE'. | 'ACTIVE', 'INACTIVE' |


## Join Paths & Relationships
- `dim_member.tier_id -> dim_member_tier.tier_id`
- `dim_member.member_id -> fact_transaction.member_id`
- `dim_member.member_id -> fact_points_ledger.member_id`

## Cost & Query Guidance
> [!IMPORTANT]
> Dimension table (~50,000 rows). Can be joined freely with fact tables.

Related concepts:
- [Loyalty POC Dataset](/datasets/loyalty_poc/index.md)
- [vw_member_transactions View](/datasets/loyalty_poc/views/vw_member_transactions.md)
