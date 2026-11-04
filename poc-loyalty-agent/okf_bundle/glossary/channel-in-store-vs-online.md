---
type: Business Term
title: Channel (In-Store vs Online)
description: Sales channels separating physical retail brick-and-mortar stores from digital e-commerce transactions.
tags:
  - omnichannel
  - retail
  - channels
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/dim_store.md"
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
---

# Channel (In-Store vs Online)

## Definition
Transactions are categorized into two primary channels:
1. **`STORE`**: Physical brick-and-mortar retail store locations (e.g., Doncaster, Chadstone, Sydney City). Recorded with `channel = 'STORE'` and `store_id != 'S16'`.
2. **`ONLINE`**: Digital e-commerce website and mobile application orders. Recorded with `channel = 'ONLINE'` and `store_id = 'S16'`.

## Channel Metrics
- **Channel Propensity**: Share of transactions or member spend fulfilled via online versus store:
  ```sql
  SAFE_DIVIDE(COUNTIF(channel = 'ONLINE'), COUNT(*)) AS online_txn_share
  ```
- Relevant for [UC3: Age Band Store vs Online](/use-cases/uc03-age-band-store-vs-online.md) and [UC4a: Online vs In-Store Spend Break-up](/use-cases/uc04a-online-vs-store-spend-split.md).

