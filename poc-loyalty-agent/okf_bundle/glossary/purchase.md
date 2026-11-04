---
type: Business Term
title: Purchase
description: A completed retail sales transaction by a loyalty member recorded in the point-of-sale or digital system.
tags:
  - transactions
  - sales
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/metrics/purchase-count.md"
---

# Purchase

## Definition
A **Purchase** represents an executed order in `fact_transaction`, identified uniquely by `transaction_id`.

## Counting Standard
- When ranking or counting purchases (e.g. UC1a: "Of those 100, rank by number of purchases"), calculate `COUNT(DISTINCT transaction_id)`.
- Line items within the basket are tracked in `fact_transaction_line` and do not increase the purchase count.

## Related Concepts
- [Visit](/glossary/visit.md)
- [Purchase Count Metric](/metrics/purchase-count.md)

