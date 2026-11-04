---
type: Business Term
title: Visit
description: A distinct customer shopping occasion occurring either in-store or online on a given date.
tags:
  - loyalty
  - engagement
  - frequency
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/metrics/avg-visit-spend.md"
---

# Visit

## Definition
A **Visit** corresponds to an individual shopping occasion by a loyalty member.

## Business Rules & Grain
1. **Visit Grain**: For loyalty analytics in this POC, a visit is measured as a distinct transaction event or member shopping session on a given calendar day:
   - Canonical expression: `COUNT(DISTINCT transaction_id)` or `COUNT(transaction_id)`.
2. **Same-Day Visits**: If a customer completes two separate transactions in the same store at different times, they may count as 2 separate basket purchases or 1 member shopping day depending on the use case. For UC2 (Average Visit Spend), each distinct transaction is treated as a visit occasion. For UC7 (Staff multi-transaction days), multiple transactions on the same calendar date are explicitly isolated.

## Related Concepts
- [Purchase](/glossary/purchase.md)
- [Average Visit Spend](/metrics/avg-visit-spend.md)
- [High Frequency](/glossary/high-frequency.md)

