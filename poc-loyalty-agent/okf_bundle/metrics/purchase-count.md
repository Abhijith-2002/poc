---
type: Metric
title: Purchase Count
description: Count of completed purchase transactions by a loyalty member.
tags:
  - metric
  - orders
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/glossary/purchase.md"
---

# Purchase Count

## Formula
$$\text{Purchase Count} = \text{COUNT(DISTINCT transaction\_id)}$$

## Canonical BigQuery SQL Expression
```sql
COUNT(DISTINCT transaction_id)
```

## Usage
Used in [UC1a: Rank by Number of Purchases](/use-cases/uc01a-rank-by-purchases.md) to re-order the top 100 Doncaster spenders.

