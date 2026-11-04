# Loyalty POC Dataset (`loyalty_poc`)

The `loyalty_poc` dataset represents a complete retail customer loyalty analytics schema modeled in Google Cloud BigQuery.

## Architectural Highlights
- **High-Performance Partitioning**: Partitioned on `transaction_date` (DAILY) for `fact_transaction`, preventing full table scans.
- **Clustering**: Clustered by `member_id` and `store_id` to optimize customer cohort lookups and store-level aggregations.
- **Semantic Denormalization**: A pre-joined view `vw_member_transactions` simplifies analytical queries and lowers execution cost.

## Table Inventory
1. [dim_member](/datasets/loyalty_poc/tables/dim_member.md): Customer profiles, contactability, demographics, and loyalty tiers.
2. [dim_member_tier](/datasets/loyalty_poc/tables/dim_member_tier.md): Tier thresholds and multipliers.
3. [dim_store](/datasets/loyalty_poc/tables/dim_store.md): Retail stores and digital pseudo-store (`ONLINE`).
4. [fact_transaction](/datasets/loyalty_poc/tables/fact_transaction.md): Sales transactions with total spend, items count, and points earned.
5. [fact_transaction_line](/datasets/loyalty_poc/tables/fact_transaction_line.md): Itemized line items and product categories.
6. [fact_points_ledger](/datasets/loyalty_poc/tables/fact_points_ledger.md): Historical points ledger events.
7. [dim_date](/datasets/loyalty_poc/tables/dim_date.md): Calendar dimension with holiday attributes.
8. [vw_member_transactions](/datasets/loyalty_poc/views/vw_member_transactions.md): Denormalized analysis view.

