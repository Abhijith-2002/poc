---
type: Metric
title: Online Spend Share
description: Proportion of total member spend executed through the digital online channel.
tags:
  - metric
  - digital
  - channel-share
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/glossary/channel-in-store-vs-online.md"
---

# Online Spend Share

## Formula
$$\text{Online Spend Share} = \frac{\sum_{\text{channel} = \text{'ONLINE'}} \text{total\_amount}}{\sum \text{total\_amount}} \times 100\%$$

## Canonical BigQuery SQL Expression
```sql
ROUND(SAFE_DIVIDE(SUM(CASE WHEN channel = 'ONLINE' THEN total_amount ELSE 0 END), SUM(total_amount)) * 100.0, 2)
```

## Usage
Used in [UC4a: Online vs Store Spend Split](/use-cases/uc04a-online-vs-store-spend-split.md).

