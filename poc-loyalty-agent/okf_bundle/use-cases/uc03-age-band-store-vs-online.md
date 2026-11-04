---
type: Use Case
use_case_id: UC3
title: Which age band is more likely to shop in store vs online past 6 months
description: Evaluates transaction and spend propensity between physical stores and digital channels across age bands over the past 6 months.
runtime: bigquery
parameters:
  - name: window_months
    type: integer
    default: 6
    required: true
    description: "Trailing months observation window."
output_columns:
  - name: age_band
    type: string
  - name: store_txn_count
    type: integer
  - name: online_txn_count
    type: integer
  - name: store_spend
    type: float
  - name: online_spend
    type: float
  - name: store_share_pct
    type: float
  - name: online_share_pct
    type: float
  - name: preferred_channel
    type: string
visualization: none
validation:
  min_rows: 6
  max_rows: 6
  assertions:
    - "store_share_pct + online_share_pct BETWEEN 99.0 AND 101.0"
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/datasets/loyalty_poc/tables/dim_member.md"
  - "/glossary/age-band.md"
  - "/glossary/channel-in-store-vs-online.md"
---

# UC3: Age Band Store vs Online Shopping Propensity

## 1. Intent & Example Questions
- "Which age band is more likely to shop in store vs online, past 6 months?"
- "Compare digital vs brick-and-mortar shopping preferences across age bands over the last 6 months."
- "What demographic age group prefers shopping online compared to in physical retail stores?"

## 2. Parameters & Defaults
- `@window_months` (INT64, default: `6`): Trailing months observation window.

## 3. Business Rules & Definitions
- Grouped by [Age Band](/glossary/age-band.md) (`'18-24'`, `'25-34'`, `'35-44'`, `'45-54'`, `'55-64'`, `'65+'`).
- Channel classified by [Channel Definition](/glossary/channel-in-store-vs-online.md) (`channel = 'STORE'` vs `channel = 'ONLINE'`).
- Bounded by `transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)`.
- Calculates percentage share of transactions:
  $$\text{store\_share\_pct} = \frac{\text{store txns}}{\text{total txns}} \times 100\%$$
- The age band with highest `store_share_pct` is identified as most likely to shop in store; highest `online_share_pct` as most likely online.

## 4. Canonical BigQuery SQL Template
```sql
WITH channel_summary AS (
  SELECT
    m.age_band,
    COUNTIF(t.channel = 'STORE') AS store_txn_count,
    COUNTIF(t.channel = 'ONLINE') AS online_txn_count,
    ROUND(SUM(CASE WHEN t.channel = 'STORE' THEN t.total_amount ELSE 0 END), 2) AS store_spend,
    ROUND(SUM(CASE WHEN t.channel = 'ONLINE' THEN t.total_amount ELSE 0 END), 2) AS online_spend,
    COUNT(t.transaction_id) AS total_txns
  FROM `${PROJECT}.${DATASET}.fact_transaction` t
  JOIN `${PROJECT}.${DATASET}.dim_member` m ON t.member_id = m.member_id
  WHERE t.transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL @window_months MONTH)
  GROUP BY m.age_band
)
SELECT
  age_band,
  store_txn_count,
  online_txn_count,
  store_spend,
  online_spend,
  ROUND(SAFE_DIVIDE(store_txn_count, total_txns) * 100.0, 2) AS store_share_pct,
  ROUND(SAFE_DIVIDE(online_txn_count, total_txns) * 100.0, 2) AS online_share_pct,
  CASE
    WHEN store_txn_count >= online_txn_count THEN 'STORE'
    ELSE 'ONLINE'
  END AS preferred_channel
FROM channel_summary
ORDER BY store_share_pct DESC;
```

## 5. Chained / Follow-Up Variants
- Followed by [UC3a: Average Store Visits for Top Age Band](/use-cases/uc03a-top-age-band-store-visits.md) which inspects store visit frequency for the top band identified.

## 6. Output Format & Visualization Specification
- **Visualization**: `none` (tabular summary + explicit analytical takeaway identifying top in-store band and top online band).

## 7. Edge Cases, Pitfalls & Interpretation Notes
- Senior demographics (`65+`) typically display high in-store propensity (> 80%), whereas young adults (`18-24`) display high online propensity (> 65%).

