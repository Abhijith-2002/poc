#!/usr/bin/env python3
"""
scripts/build_okf_bundle.py
Assembles and generates OKF v0.2 table and view concepts programmatically
from schema metadata to prevent documentation drift.
"""

import os
import sys

TABLE_METADATA = {
    "dim_member": {
        "title": "Member Dimension (dim_member)",
        "description": "Retail loyalty programme customer profiles, contactability flags, demographics, and membership tier.",
        "primary_key": "member_id",
        "grain": "One row per enrolled loyalty member.",
        "partitioning": "None",
        "clustering": "None",
        "join_paths": [
            "dim_member.tier_id -> dim_member_tier.tier_id",
            "dim_member.member_id -> fact_transaction.member_id",
            "dim_member.member_id -> fact_points_ledger.member_id",
        ],
        "cost_notes": "Dimension table (~50,000 rows). Can be joined freely with fact tables.",
        "columns": [
            ("member_id", "STRING", "Primary key. Unique member identifier (e.g. M000001).", "Required"),
            ("first_name", "STRING", "Member given name. Classified as PII.", "Required"),
            ("last_name", "STRING", "Member surname. Classified as PII.", "Required"),
            ("email", "STRING", "Email address. Classified as PII.", "Optional/Nullable"),
            ("email_opt_in", "BOOLEAN", "Explicit consent to receive marketing emails.", "TRUE / FALSE"),
            ("sms_opt_in", "BOOLEAN", "Explicit consent to receive SMS marketing messages.", "TRUE / FALSE"),
            ("contactable_by_email", "BOOLEAN", "Precomputed flag: email present AND email_opt_in = TRUE.", "TRUE / FALSE"),
            ("date_of_birth", "DATE", "Member date of birth (YYYY-MM-DD).", "Historical date"),
            ("age", "INTEGER", "Calculated member age in years.", "18 to 90"),
            ("age_band", "STRING", "Standard age band: '18-24', '25-34', '35-44', '45-54', '55-64', '65+'.", "Standard bands"),
            ("gender", "STRING", "Member gender: 'F', 'M', 'Other'.", "Category"),
            ("state", "STRING", "Australian state of residence ('VIC', 'NSW', 'QLD', etc.).", "Category"),
            ("postcode", "STRING", "Australian 4-digit residential postcode.", "Numeric string"),
            ("join_date", "DATE", "Date member enrolled in the loyalty programme.", "Historical date"),
            ("tier_id", "INTEGER", "Foreign key to dim_member_tier.tier_id (1: Bronze, 2: Silver, 3: Gold, 4: Platinum).", "1 to 4"),
            ("tier_name", "STRING", "Denormalized loyalty tier name.", "Bronze, Silver, Gold, Platinum"),
            ("points_balance", "INTEGER", "Current accrued loyalty points balance.", ">= 0"),
            ("staff_indicator", "STRING", "'Y' if employee/staff member, 'N' if regular customer.", "'Y' or 'N'"),
            ("status", "STRING", "Account status: 'ACTIVE' or 'INACTIVE'.", "'ACTIVE', 'INACTIVE'"),
        ]
    },
    "dim_member_tier": {
        "title": "Loyalty Tier Dimension (dim_member_tier)",
        "description": "Loyalty tiers, spend qualification thresholds, and points accrual multipliers.",
        "primary_key": "tier_id",
        "grain": "One row per loyalty tier level.",
        "partitioning": "None",
        "clustering": "None",
        "join_paths": [
            "dim_member_tier.tier_id -> dim_member.tier_id"
        ],
        "cost_notes": "Static reference lookup table (4 rows). Negligible scan cost.",
        "columns": [
            ("tier_id", "INTEGER", "Primary key (1: Bronze, 2: Silver, 3: Gold, 4: Platinum).", "1, 2, 3, 4"),
            ("tier_name", "STRING", "Tier level name.", "'Bronze', 'Silver', 'Gold', 'Platinum'"),
            ("threshold_spend", "NUMERIC", "Annual spend threshold to achieve or retain tier.", ">= 0.0"),
            ("points_multiplier", "NUMERIC", "Points earned per dollar spent.", "1.0 to 2.0"),
            ("benefits", "STRING", "Summary of tier perks (shipping, VIP events, gifts).", "Text"),
        ]
    },
    "dim_store": {
        "title": "Store Dimension (dim_store)",
        "description": "Retail brick-and-mortar stores and digital pseudo-store locations.",
        "primary_key": "store_id",
        "grain": "One row per physical or digital retail storefront.",
        "partitioning": "None",
        "clustering": "None",
        "join_paths": [
            "dim_store.store_id -> fact_transaction.store_id"
        ],
        "cost_notes": "Small reference table (16 rows).",
        "columns": [
            ("store_id", "STRING", "Primary key. Store identifier (e.g. S01, S02, S16).", "Unique store code"),
            ("store_name", "STRING", "Store name (e.g. 'Doncaster', 'Chadstone', 'ONLINE').", "Location name"),
            ("state", "STRING", "State jurisdiction or 'National' for online.", "'VIC', 'NSW', 'QLD', etc."),
            ("region", "STRING", "Geographical sales region (e.g. 'Metro East', 'Digital').", "Region category"),
            ("channel_type", "STRING", "Channel classification: 'STORE' or 'ONLINE'.", "'STORE', 'ONLINE'"),
        ]
    },
    "dim_date": {
        "title": "Date Dimension (dim_date)",
        "description": "Calendar dimension containing day, month, quarter, year, and holiday flags.",
        "primary_key": "date_key",
        "grain": "One row per calendar date.",
        "partitioning": "None",
        "clustering": "None",
        "join_paths": [
            "dim_date.full_date -> fact_transaction.transaction_date"
        ],
        "cost_notes": "Calendar lookup table (1,826 rows).",
        "columns": [
            ("date_key", "INTEGER", "Surrogate integer key in YYYYMMDD format.", "YYYYMMDD"),
            ("full_date", "DATE", "Actual calendar date.", "Date"),
            ("day_of_week", "INTEGER", "Day of week (1=Monday .. 7=Sunday).", "1 to 7"),
            ("day_name", "STRING", "Day name (Monday, Tuesday, etc.).", "Day name"),
            ("day_of_month", "INTEGER", "Day of month (1 to 31).", "1 to 31"),
            ("month_num", "INTEGER", "Month number (1 to 12).", "1 to 12"),
            ("month_name", "STRING", "Month name (January, February, etc.).", "Month name"),
            ("quarter", "INTEGER", "Calendar quarter (1 to 4).", "1 to 4"),
            ("year", "INTEGER", "Calendar year (e.g. 2025, 2026).", "Year"),
            ("is_weekend", "BOOLEAN", "TRUE if Saturday or Sunday.", "TRUE / FALSE"),
            ("is_holiday", "BOOLEAN", "TRUE if major public holiday.", "TRUE / FALSE"),
        ]
    },
    "fact_transaction": {
        "title": "Transaction Fact (fact_transaction)",
        "description": "Sales transactions recorded across retail stores and digital e-commerce channels.",
        "primary_key": "transaction_id",
        "grain": "One row per sales transaction order.",
        "partitioning": "PARTITION BY transaction_date (DAILY). Partition pruning is mandatory.",
        "clustering": "CLUSTER BY member_id, store_id.",
        "join_paths": [
            "fact_transaction.member_id -> dim_member.member_id",
            "fact_transaction.store_id -> dim_store.store_id",
            "fact_transaction.transaction_date -> dim_date.full_date",
            "fact_transaction.transaction_id -> fact_transaction_line.transaction_id",
        ],
        "cost_notes": "Core fact table (~1.5M rows). ALWAYS filter queries on transaction_date to avoid full partition scans.",
        "columns": [
            ("transaction_id", "STRING", "Primary key. Unique transaction order identifier.", "Unique TXN code"),
            ("member_id", "STRING", "Foreign key to dim_member.member_id.", "Foreign key"),
            ("store_id", "STRING", "Foreign key to dim_store.store_id (e.g. 'S01' Doncaster, 'S16' ONLINE).", "Foreign key"),
            ("channel", "STRING", "Channel used: 'STORE' or 'ONLINE'.", "'STORE', 'ONLINE'"),
            ("transaction_ts", "TIMESTAMP", "Exact timestamp when transaction completed.", "Timestamp (UTC)"),
            ("transaction_date", "DATE", "Partitioning key. Calendar date of transaction.", "Date"),
            ("total_amount", "NUMERIC", "Final monetary amount paid (net of discounts).", "Currency (> 0.0)"),
            ("discount_amount", "NUMERIC", "Total promotional or staff discount applied.", "Currency (>= 0.0)"),
            ("items_count", "INTEGER", "Number of distinct items/units in basket.", ">= 1"),
            ("points_earned", "INTEGER", "Loyalty points awarded on this transaction.", ">= 0"),
            ("payment_type", "STRING", "Tender method (CREDIT_CARD, APPLE_PAY, AFTERPAY, etc.).", "Payment category"),
        ]
    },
    "fact_transaction_line": {
        "title": "Transaction Line Item Fact (fact_transaction_line)",
        "description": "Itemized line items and product categories purchased within a transaction.",
        "primary_key": "line_id",
        "grain": "One row per product category line within a transaction.",
        "partitioning": "None",
        "clustering": "CLUSTER BY transaction_id.",
        "join_paths": [
            "fact_transaction_line.transaction_id -> fact_transaction.transaction_id"
        ],
        "cost_notes": "Line item fact table (~1.6M rows). Join with fact_transaction when category breakdown is needed.",
        "columns": [
            ("line_id", "STRING", "Primary key. Unique basket line item identifier.", "Unique Line code"),
            ("transaction_id", "STRING", "Foreign key to fact_transaction.transaction_id.", "Foreign key"),
            ("product_category", "STRING", "Merchandise category ('Apparel', 'Footwear', 'Beauty', 'Home', etc.).", "Category"),
            ("quantity", "INTEGER", "Quantity of units purchased in line.", ">= 1"),
            ("line_amount", "NUMERIC", "Line-item subtotal monetary spend.", "Currency (> 0.0)"),
        ]
    },
    "fact_points_ledger": {
        "title": "Points Ledger Fact (fact_points_ledger)",
        "description": "Historical audit ledger of loyalty points accrued, redeemed, expired, or adjusted.",
        "primary_key": "ledger_id",
        "grain": "One row per points balance mutation event.",
        "partitioning": "PARTITION BY DATE(event_ts)",
        "clustering": "CLUSTER BY member_id.",
        "join_paths": [
            "fact_points_ledger.member_id -> dim_member.member_id"
        ],
        "cost_notes": "Audit table tracking points history (~375k rows).",
        "columns": [
            ("ledger_id", "STRING", "Primary key. Unique points event identifier.", "Unique PL code"),
            ("member_id", "STRING", "Foreign key to dim_member.member_id.", "Foreign key"),
            ("event_ts", "TIMESTAMP", "Exact timestamp when points mutation occurred.", "Timestamp"),
            ("event_type", "STRING", "Mutation type ('EARN', 'REDEEM', 'EXPIRE', 'ADJUST').", "Category"),
            ("points", "INTEGER", "Points value added or subtracted.", "Integer (+/-)"),
            ("balance_after", "INTEGER", "Cumulative member points balance immediately following event.", ">= 0"),
        ]
    }
}


def generate_table_concepts(output_dir: str):
    tables_dir = os.path.join(output_dir, "datasets", "loyalty_poc", "tables")
    os.makedirs(tables_dir, exist_ok=True)
    
    for table_name, meta in TABLE_METADATA.items():
        file_path = os.path.join(tables_dir, f"{table_name}.md")
        cols_table = "| Column | Data Type | Description | Values / Nullable |\n|---|---|---|---|\n"
        for col_name, col_type, col_desc, col_vals in meta["columns"]:
            cols_table += f"| `{col_name}` | `{col_type}` | {col_desc} | {col_vals} |\n"
            
        join_paths_str = "\n".join(f"- `{jp}`" for jp in meta["join_paths"])
        
        content = f"""---
type: BigQuery Table
resource: bigquery://${{PROJECT}}/${{DATASET}}/{table_name}
title: "{meta['title']}"
description: "{meta['description']}"
tags:
  - bigquery
  - schema
  - {table_name}
status: stable
generated:
  by: okf-schema-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/index.md"
---

# {meta['title']}

## Overview
{meta['description']}

- **Resource URI**: `bigquery://${{PROJECT}}/${{DATASET}}/{table_name}`
- **Grain**: {meta['grain']}
- **Primary Key**: `{meta['primary_key']}`
- **Partitioning**: {meta['partitioning']}
- **Clustering**: {meta['clustering']}

## Column Specifications
{cols_table}

## Join Paths & Relationships
{join_paths_str}

## Cost & Query Guidance
> [!IMPORTANT]
> {meta['cost_notes']}

Related concepts:
- [Loyalty POC Dataset](/datasets/loyalty_poc/index.md)
- [vw_member_transactions View](/datasets/loyalty_poc/views/vw_member_transactions.md)
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated table concept: {file_path}")

    # Generate View Concept
    views_dir = os.path.join(output_dir, "datasets", "loyalty_poc", "views")
    os.makedirs(views_dir, exist_ok=True)
    view_path = os.path.join(views_dir, "vw_member_transactions.md")
    view_content = """---
type: BigQuery View
resource: bigquery://${PROJECT}/${DATASET}/vw_member_transactions
title: "Denormalized Member Transactions View (vw_member_transactions)"
description: "Pre-joined view joining transactions with member demographics, tier attributes, and store locations."
tags:
  - bigquery
  - view
  - vw_member_transactions
status: stable
generated:
  by: okf-schema-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/fact_transaction.md"
  - "/datasets/loyalty_poc/tables/dim_member.md"
  - "/datasets/loyalty_poc/tables/dim_store.md"
---

# Denormalized Member Transactions View (`vw_member_transactions`)

## Overview
`vw_member_transactions` flattens transactions with member demographics and store attributes, providing an optimized, easy-to-query dataset for analytical use cases.

## Underlying SQL Definition
```sql
SELECT
  t.transaction_id,
  t.member_id,
  t.store_id,
  t.channel,
  t.transaction_ts,
  t.transaction_date,
  t.total_amount,
  t.discount_amount,
  t.items_count,
  t.points_earned,
  t.payment_type,
  m.first_name,
  m.last_name,
  m.email,
  m.contactable_by_email,
  m.age,
  m.age_band,
  m.gender,
  m.state AS member_state,
  m.join_date,
  m.tier_id,
  m.tier_name,
  m.staff_indicator,
  s.store_name,
  s.state AS store_state,
  s.channel_type
FROM `${PROJECT}.${DATASET}.fact_transaction` t
LEFT JOIN `${PROJECT}.${DATASET}.dim_member` m ON t.member_id = m.member_id
LEFT JOIN `${PROJECT}.${DATASET}.dim_store` s ON t.store_id = s.store_id
```

## Key Grain & Cost Guidance
- **Grain**: One row per sales transaction.
- **Partition Filtering**: Filters on `transaction_date` are pushed directly down to `fact_transaction`, maintaining optimal partition pruning and lowest query cost.
"""
    with open(view_path, "w", encoding="utf-8") as f:
        f.write(view_content)
    print(f"Generated view concept: {view_path}")


if __name__ == "__main__":
    bundle_dir = sys.argv[1] if len(sys.argv) > 1 else "okf_bundle"
    generate_table_concepts(bundle_dir)

