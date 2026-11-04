---
type: Business Term
title: High Frequency Member
description: Threshold definition for frequent transaction activity among newly enrolled members.
tags:
  - loyalty
  - frequency
  - onboarding
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/datasets/loyalty_poc/tables/dim_member.md"
---

# High Frequency Member

## Definition
For customers who joined in the last 6 months (UC4), **high visit frequency** is defined as members who have recorded:
- At least 5 or more distinct transactions/visits (`visit_count >= 5`) within their first 6 months since joining.
- Or top decile transaction count among the new joiner cohort.

## Canonical Expression
```sql
COUNT(t.transaction_id) >= @min_visits  -- Default min_visits = 5
```

