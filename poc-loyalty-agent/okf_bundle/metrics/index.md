# Metrics Catalog

This catalog documents standard analytical metrics, formulas, BigQuery SQL expressions, and grain definitions for loyalty calculations.

## Metric Directory
- [Total Spend](/metrics/total-spend.md): Aggregated monetary sales value (`SUM(total_amount)`).
- [Average Visit Spend](/metrics/avg-visit-spend.md): Mean spend per shopping visit (`SUM(total_amount) / COUNT(transaction_id)`).
- [Visit Frequency](/metrics/visit-frequency.md): Number of shopping occasions per member in a given timeframe.
- [Purchase Count](/metrics/purchase-count.md): Total number of distinct purchases (`COUNT(DISTINCT transaction_id)`).
- [Online Spend Share](/metrics/online-spend-share.md): Percentage of spend through the online digital channel.

