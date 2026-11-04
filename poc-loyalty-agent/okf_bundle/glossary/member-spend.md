---
type: Business Term
title: Member Spend
description: Gross monetary value of transactions associated with a loyalty member before or after discounts.
tags:
  - loyalty
  - revenue
  - finance
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/metrics/total-spend.md"
---

# Member Spend

## Definition
**Member Spend** represents the total financial amount spent by an enrolled loyalty member on completed transactions.

## Business Rules
1. In `fact_transaction`, member spend is represented by `total_amount` (net of line discounts).
2. For analytical reporting across rolling periods (e.g., last 12 months, calendar YTD), spend must be aggregated using `SUM(total_amount)` filtered on `transaction_date`.
3. Unattached or guest transactions (where `member_id` is null) are excluded from member loyalty spend metrics.

## Related Concepts
- [Total Spend Metric](/metrics/total-spend.md)
- [Average Visit Spend Metric](/metrics/avg-visit-spend.md)
- [fact_transaction](/datasets/loyalty_poc/tables/fact_transaction.md)

