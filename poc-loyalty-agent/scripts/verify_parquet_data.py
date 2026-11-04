#!/usr/bin/env python3
"""
scripts/verify_parquet_data.py
Phase 1 verification script: validates row counts, null constraints, referential integrity,
and runs assertion queries for all 12 use cases against the generated Parquet datasets.
"""

import datetime
import os
import sys
import pandas as pd
import pyarrow.parquet as pq


def verify_data(data_dir: str = "data/parquet", end_date_str: str = "2026-11-03"):
    print("=== Phase 1 Verification: Validating Synthetic Data ===")
    end_date = datetime.date.fromisoformat(end_date_str)
    
    # 1. Load tables
    print(f"Reading Parquet tables from {data_dir}...")
    df_member = pq.read_table(os.path.join(data_dir, "dim_member.parquet")).to_pandas()
    df_tier = pq.read_table(os.path.join(data_dir, "dim_member_tier.parquet")).to_pandas()
    df_store = pq.read_table(os.path.join(data_dir, "dim_store.parquet")).to_pandas()
    df_date = pq.read_table(os.path.join(data_dir, "dim_date.parquet")).to_pandas()
    df_txn = pq.read_table(os.path.join(data_dir, "fact_transaction.parquet")).to_pandas()
    df_line = pq.read_table(os.path.join(data_dir, "fact_transaction_line.parquet")).to_pandas()
    df_ledger = pq.read_table(os.path.join(data_dir, "fact_points_ledger.parquet")).to_pandas()

    # 2. Check row counts
    print(f"dim_member: {len(df_member):,} rows")
    print(f"dim_member_tier: {len(df_tier):,} rows")
    print(f"dim_store: {len(df_store):,} rows")
    print(f"dim_date: {len(df_date):,} rows")
    print(f"fact_transaction: {len(df_txn):,} rows")
    print(f"fact_transaction_line: {len(df_line):,} rows")
    print(f"fact_points_ledger: {len(df_ledger):,} rows")

    assert len(df_member) >= 50000, f"Expected >= 50k members, got {len(df_member)}"
    assert len(df_tier) == 4, f"Expected 4 tiers, got {len(df_tier)}"
    assert len(df_store) >= 16, f"Expected >= 16 stores, got {len(df_store)}"
    assert len(df_txn) >= 1500000, f"Expected >= 1.5M transactions, got {len(df_txn)}"
    assert len(df_line) > 0, "fact_transaction_line is empty"
    assert len(df_ledger) > 0, "fact_points_ledger is empty"
    print("✓ Row counts verified.")

    # 3. Check nulls on critical columns
    assert df_member["member_id"].notna().all(), "Null found in dim_member.member_id"
    assert df_txn["transaction_id"].notna().all(), "Null found in fact_transaction.transaction_id"
    assert df_txn["member_id"].notna().all(), "Null found in fact_transaction.member_id"
    assert df_txn["transaction_date"].notna().all(), "Null found in fact_transaction.transaction_date"
    assert df_txn["total_amount"].notna().all(), "Null found in fact_transaction.total_amount"
    print("✓ Null checks verified.")

    # 4. Referential integrity
    member_id_set = set(df_member["member_id"])
    store_id_set = set(df_store["store_id"])
    tier_id_set = set(df_tier["tier_id"])

    assert set(df_txn["member_id"]).issubset(member_id_set), "Orphan member_id found in fact_transaction!"
    assert set(df_txn["store_id"]).issubset(store_id_set), "Orphan store_id found in fact_transaction!"
    assert set(df_member["tier_id"]).issubset(tier_id_set), "Orphan tier_id found in dim_member!"
    print("✓ Referential integrity verified.")

    # 5. Use Case Assertions
    print("\n--- Running Use Case Assertions ---")
    
    # Pre-join denormalized view for fast pandas checks
    df_merged = df_txn.merge(df_member[["member_id", "email", "contactable_by_email", "age_band", "gender", "state", "tier_id", "tier_name", "staff_indicator", "join_date"]], on="member_id", how="left")
    df_merged = df_merged.merge(df_store[["store_id", "store_name", "channel_type"]], on="store_id", how="left")
    df_merged["transaction_date"] = pd.to_datetime(df_merged["transaction_date"]).dt.date
    
    twelve_months_ago = end_date - datetime.timedelta(days=365)
    six_months_ago = end_date - datetime.timedelta(days=180)
    three_months_ago = end_date - datetime.timedelta(days=90)
    two_months_ago = end_date - datetime.timedelta(days=60)
    one_month_ago = end_date - datetime.timedelta(days=30)

    # UC1: Top 100 members by spend in last 12 months at Doncaster contactable by email
    df_uc1 = df_merged[
        (df_merged["transaction_date"] >= twelve_months_ago) &
        (df_merged["store_name"] == "Doncaster") &
        (df_merged["contactable_by_email"] == True)
    ].groupby("member_id").agg(total_spend=("total_amount", "sum"), purchase_count=("transaction_id", "count")).reset_index()
    df_uc1 = df_uc1.sort_values(by="total_spend", ascending=False).head(100)
    print(f"UC1 Doncaster Spenders count: {len(df_uc1)}")
    assert len(df_uc1) == 100, f"Expected 100 members for UC1, got {len(df_uc1)}"
    print("✓ UC1 Assertion passed.")

    # UC1a: Ranked by number of purchases
    df_uc1a = df_uc1.sort_values(by="purchase_count", ascending=False)
    assert len(df_uc1a) == 100, "UC1a should have 100 rows"
    print("✓ UC1a Assertion passed.")

    # UC2: Average visit spend per member broken down by tier, past 3 months
    df_uc2_raw = df_merged[df_merged["transaction_date"] >= three_months_ago]
    # visit = distinct member_id + transaction_date (or transaction)
    df_uc2 = df_uc2_raw.groupby("tier_name").agg(
        total_spend=("total_amount", "sum"),
        total_visits=("transaction_id", "count")
    ).reset_index()
    df_uc2["avg_visit_spend"] = df_uc2["total_spend"] / df_uc2["total_visits"]
    print(f"UC2 Avg Visit Spend by Tier:\n{df_uc2[['tier_name', 'avg_visit_spend']]}")
    assert len(df_uc2) == 4, f"Expected 4 tiers in UC2, got {len(df_uc2)}"
    assert (df_uc2["avg_visit_spend"] > 0).all(), "UC2 visit spend should be positive"
    print("✓ UC2 & UC2a Assertion passed.")

    # UC3: Age band shop in store vs online, past 6 months
    df_uc3_raw = df_merged[df_merged["transaction_date"] >= six_months_ago]
    df_uc3 = df_uc3_raw.groupby(["age_band", "channel"]).agg(
        txn_count=("transaction_id", "count"),
        total_spend=("total_amount", "sum")
    ).reset_index()
    df_uc3_pivot = df_uc3.pivot(index="age_band", columns="channel", values="txn_count").fillna(0)
    df_uc3_pivot["online_share"] = df_uc3_pivot["ONLINE"] / (df_uc3_pivot["ONLINE"] + df_uc3_pivot["STORE"])
    print(f"UC3 Online Share by Age Band:\n{df_uc3_pivot['online_share']}")
    assert len(df_uc3_pivot) == 6, f"Expected 6 age bands, got {len(df_uc3_pivot)}"
    # 18-24 should be high online, 65+ high store
    assert df_uc3_pivot.loc["18-24", "online_share"] > 0.5, "18-24 should be predominantly online"
    assert df_uc3_pivot.loc["65+", "online_share"] < 0.35, "65+ should be predominantly store"
    print("✓ UC3 & UC3a Assertion passed.")

    # UC4: Top 100 members joined in last 6 months with high visit frequency, ranked by spend
    df_uc4_raw = df_merged[
        (df_merged["join_date"] >= six_months_ago) &
        (df_merged["transaction_date"] >= six_months_ago)
    ]
    df_uc4_agg = df_uc4_raw.groupby("member_id").agg(
        visit_count=("transaction_id", "count"),
        total_spend=("total_amount", "sum")
    ).reset_index()
    # High frequency: visit_count >= 5
    df_uc4 = df_uc4_agg[df_uc4_agg["visit_count"] >= 5].sort_values(by="total_spend", ascending=False).head(100)
    print(f"UC4 High Frequency New Joiners count: {len(df_uc4)}")
    assert len(df_uc4) >= 50, f"Expected >= 50 qualifying members for UC4, got {len(df_uc4)}"
    print("✓ UC4 & UC4a Assertion passed.")

    # UC5: Chart spend by tier this year vs last year (green when up, red when down)
    df_merged["year"] = pd.to_datetime(df_merged["transaction_date"]).dt.year
    cur_year = end_date.year
    prev_year = cur_year - 1
    # Compare same day/month range (YTD)
    df_ytd = df_merged[
        ((df_merged["year"] == cur_year) & (df_merged["transaction_date"] <= end_date)) |
        ((df_merged["year"] == prev_year) & (df_merged["transaction_date"] <= datetime.date(prev_year, end_date.month, end_date.day)))
    ]
    df_uc5 = df_ytd.groupby(["tier_name", "year"]).agg(spend=("total_amount", "sum")).reset_index()
    df_uc5_p = df_uc5.pivot(index="tier_name", columns="year", values="spend").fillna(0)
    df_uc5_p["diff"] = df_uc5_p[cur_year] - df_uc5_p[prev_year]
    print(f"UC5 YoY Spend Diff by Tier:\n{df_uc5_p[[prev_year, cur_year, 'diff']]}")
    assert (df_uc5_p["diff"] > 0).any(), "Expected at least one tier spend UP (green)"
    assert (df_uc5_p["diff"] < 0).any(), "Expected at least one tier spend DOWN (red)"
    print("✓ UC5 Assertion passed (both positive and negative YoY variances present).")

    # UC6: Demographic breakdown of members who have NOT spent in last 6 months vs those who have
    recent_spenders = set(df_merged[df_merged["transaction_date"] >= six_months_ago]["member_id"])
    df_member["spent_last_6m"] = df_member["member_id"].isin(recent_spenders)
    uc6_dormant_count = (~df_member["spent_last_6m"]).sum()
    uc6_active_count = df_member["spent_last_6m"].sum()
    print(f"UC6 Active members (spent last 6m): {uc6_active_count:,} | Dormant members (not spent): {uc6_dormant_count:,}")
    assert uc6_dormant_count >= 1000, f"Expected >= 1000 dormant members, got {uc6_dormant_count}"
    assert uc6_active_count >= 30000, f"Expected >= 30000 active members, got {uc6_active_count}"
    print("✓ UC6 Assertion passed.")

    # UC7: Top 100 staff with high transaction frequency, including days with multiple transactions in last month
    df_uc7_raw = df_merged[
        (df_merged["staff_indicator"] == "Y") &
        (df_merged["transaction_date"] >= one_month_ago)
    ]
    # Count total transactions and distinct days with >1 transaction
    day_counts = df_uc7_raw.groupby(["member_id", "transaction_date"]).agg(txns_in_day=("transaction_id", "count")).reset_index()
    multi_days = day_counts[day_counts["txns_in_day"] > 1].groupby("member_id").agg(multi_txn_days=("transaction_date", "count")).reset_index()
    staff_totals = df_uc7_raw.groupby("member_id").agg(total_txns=("transaction_id", "count")).reset_index()
    df_uc7 = staff_totals.merge(multi_days, on="member_id", how="left").fillna(0)
    df_uc7 = df_uc7.sort_values(by=["total_txns", "multi_txn_days"], ascending=[False, False]).head(100)
    print(f"UC7 Top Staff with Multi-Txn Days:\n{df_uc7.head(5)}")
    assert len(df_uc7) > 0, "UC7 should return staff members"
    assert (df_uc7["multi_txn_days"] > 0).any(), "Expected staff with multiple same-day transactions in last month"
    print("✓ UC7 Assertion passed.")

    # UC8: Gold tier with points >= 3000 who haven't transacted in past 2 months
    two_month_spenders = set(df_merged[df_merged["transaction_date"] >= two_months_ago]["member_id"])
    gold_inactive = df_member[
        (df_member["tier_name"] == "Gold") &
        (df_member["points_balance"] >= 3000) &
        (~df_member["member_id"].isin(two_month_spenders))
    ]
    print(f"UC8 Gold Inactive (>= 3000 points, no txn in 2 months) Count: {len(gold_inactive)}")
    assert len(gold_inactive) > 0, "UC8 expected > 0 qualifying inactive Gold members"
    print("✓ UC8 Assertion passed.")

    print("\n=== All Phase 1 Data Validations and Use Case Assertions Passed! ===")


if __name__ == "__main__":
    verify_data()

