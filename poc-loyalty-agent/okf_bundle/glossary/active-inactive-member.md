---
type: Business Term
title: Active vs Inactive Member
description: Criteria for classifying members based on recent transaction activity or inactivity periods.
tags:
  - loyalty
  - churn
  - lifecycle
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/dim_member.md"
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
---

# Active vs Inactive Member

## Definition
Activity is evaluated relative to a sliding time window calculated from `CURRENT_DATE()`:
1. **Active Member (6-Month Activity)**: A member who has recorded at least one purchase transaction within the past 6 rolling months (`DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)`).
2. **Dormant / Inactive Member (6-Month Inactivity)**: A member with zero transactions in the past 6 months (UC6).
3. **Recent Inactivity (2-Month Inactivity)**: A member who has not transacted in the past 2 calendar months (`DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH)`), relevant for point-balance retention campaigns (UC8).

## SQL Identification Pattern
```sql
-- Members who have NOT spent in the last 6 months
SELECT m.member_id
FROM `${PROJECT}.${DATASET}.dim_member` m
LEFT JOIN `${PROJECT}.${DATASET}.fact_transaction` t
  ON m.member_id = t.member_id
  AND t.transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
WHERE t.transaction_id IS NULL
```

