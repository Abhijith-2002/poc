---
okf_version: "0.2"
title: Retail Loyalty Knowledge Bundle
description: Curated Open Knowledge Format bundle for Retail Loyalty Analytics and BigQuery deep agent navigation.
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
status: stable
---

# Retail Loyalty Knowledge Bundle (OKF v0.2)

Welcome to the Retail Loyalty Knowledge Bundle. This bundle adheres to the **Open Knowledge Format (OKF) v0.2** specification and serves as the semantic ground truth for AI agents querying the `loyalty_poc` BigQuery dataset.

## Directory Structure & Agent Navigation

- **[Datasets Catalog](/datasets/loyalty_poc/index.md)**: Physical tables, schemas, partitioning rules, and join paths.
  - [dim_member](/datasets/loyalty_poc/tables/dim_member.md): Customer loyalty members and demographics.
  - [dim_member_tier](/datasets/loyalty_poc/tables/dim_member_tier.md): Loyalty tier thresholds and multipliers.
  - [dim_store](/datasets/loyalty_poc/tables/dim_store.md): Store locations and channels (including Doncaster and ONLINE).
  - [fact_transaction](/datasets/loyalty_poc/tables/fact_transaction.md): Sales transactions partitioned by `transaction_date`.
  - [fact_transaction_line](/datasets/loyalty_poc/tables/fact_transaction_line.md): Line-level basket items and product categories.
  - [fact_points_ledger](/datasets/loyalty_poc/tables/fact_points_ledger.md): Points ledger events (EARN, REDEEM, ADJUST).
  - [dim_date](/datasets/loyalty_poc/tables/dim_date.md): Calendar dates and holiday attributes.
  - [vw_member_transactions](/datasets/loyalty_poc/views/vw_member_transactions.md): Denormalized analysis view.
- **[Business Glossary](/glossary/index.md)**: Canonical domain definitions (Spend, Visit, Purchase, Contactability, Tiers, Staff).
- **[Metrics Catalog](/metrics/index.md)**: Sanctioned analytical calculations and SQL expressions.
- **[Conventions & Governance](/conventions/index.md)**: Date window standards, SQL style, cost thresholds, PII masking, and visualization rules.
- **[Curated Use Cases](/use-cases/index.md)**: Certified analytical query templates (UC1 through UC8, with variants 1a, 2a, 3a, 4a).
- **[Question Routing](/routing/question-routing.md)**: Natural language intent-to-use-case routing matrix.

## Agent Instructions: Start Here
1. When answering user inquiries, first consult [question-routing.md](/routing/question-routing.md) to locate the sanctioned `use_case_id`.
2. Retrieve the specific use case document under `/use-cases/` and read its canonical SQL template, parameter specifications, and visualization instructions.
3. Traverse cross-links to referenced [metrics](/metrics/index.md), [glossary](/glossary/index.md), and [conventions](/conventions/index.md) to confirm calculation semantics.
4. Always enforce partition filtering on `transaction_date` and respect `MAX_BYTES_BILLED`.

