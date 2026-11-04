---
type: Metric
title: Visit Frequency
description: Count of shopping visits or transactions recorded by a member within an analytical observation window.
tags:
  - metric
  - frequency
  - engagement
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/glossary/visit.md"
---

# Visit Frequency

## Formula
$$\text{Visit Frequency} = \text{Count of Distinct Visits}$$

## Canonical BigQuery SQL Expression
```sql
COUNT(transaction_id)
```

## Usage
Used for identifying high-frequency shoppers (UC4) and staff members with high monthly transactions (UC7).

