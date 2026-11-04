#!/usr/bin/env python3
"""
scripts/create_bq_assets.py
Creates the BigQuery dataset, tables with partitioning/clustering and column descriptions,
loads synthetic Parquet datasets, and creates the view vw_member_transactions.
Uses the BigQuery Python SDK (allowed ONLY in one-off setup scripts).
"""

import os
import sys
from dotenv import load_dotenv

# Load environment settings
load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT")
DATASET_ID = os.getenv("BQ_DATASET", "loyalty_poc")
LOCATION = os.getenv("BQ_LOCATION", "US")
DATA_DIR = os.getenv("DATA_DIR", "data/parquet")


def create_and_load_assets():
    print(f"=== Creating BigQuery Assets in Project: {PROJECT_ID}, Dataset: {DATASET_ID} ===")
    
    if not PROJECT_ID or PROJECT_ID == "your-gcp-project-id":
        print("⚠️ Warning: GCP_PROJECT is not set or set to default placeholder in .env.")
        print("Please configure GCP_PROJECT in .env or run `gcloud config set project <PROJECT_ID>`.")
        print("Skipping remote BigQuery creation; local Parquet datasets are preserved for local/mock execution.")
        return

    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    except Exception as e:
        print(f"Failed to initialize BigQuery client: {e}")
        print("Ensure credentials are active via `gcloud auth application-default login`.")
        return

    # 1. Create Dataset
    dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
    try:
        dataset = client.get_dataset(dataset_ref)
        print(f"Dataset '{DATASET_ID}' already exists.")
    except Exception:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = LOCATION
        dataset.description = "Retail Customer Loyalty Analytics POC Dataset"
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"Created dataset '{DATASET_ID}' in location '{LOCATION}'.")

    # 2. Schema and Table Specifications
    tables_to_load = [
        ("dim_member_tier", "dim_member_tier.parquet", None, None),
        ("dim_store", "dim_store.parquet", None, None),
        ("dim_date", "dim_date.parquet", None, None),
        ("dim_member", "dim_member.parquet", None, None),
        ("fact_transaction", "fact_transaction.parquet", "transaction_date", ["member_id", "store_id"]),
        ("fact_transaction_line", "fact_transaction_line.parquet", None, ["transaction_id"]),
        ("fact_points_ledger", "fact_points_ledger.parquet", None, ["member_id"]),
    ]

    for table_name, parquet_file, partition_col, cluster_cols in tables_to_load:
        file_path = os.path.join(DATA_DIR, parquet_file)
        if not os.path.exists(file_path):
            print(f"❌ Parquet file not found: {file_path}. Run `python scripts/generate_data.py` first.")
            continue

        table_ref = dataset_ref.table(table_name)
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        if partition_col:
            job_config.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field=partition_col,
            )
        if cluster_cols:
            job_config.clustering_fields = cluster_cols

        print(f"Loading '{table_name}' from {file_path}...")
        with open(file_path, "rb") as source_file:
            load_job = client.load_table_from_file(source_file, table_ref, job_config=job_config)
        load_job.result()  # Wait for job to finish
        print(f"✓ Loaded {client.get_table(table_ref).num_rows:,} rows into '{table_name}'.")

    # 3. Create View: vw_member_transactions
    view_ref = dataset_ref.table("vw_member_transactions")
    view = bigquery.Table(view_ref)
    view_sql = f"""
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
    FROM `{PROJECT_ID}.{DATASET_ID}.fact_transaction` t
    LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.dim_member` m ON t.member_id = m.member_id
    LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.dim_store` s ON t.store_id = s.store_id
    """
    view.view_query = view_sql
    view.description = "Denormalized view joining transactions, members, and stores for fast analytical queries."
    
    try:
        client.delete_table(view_ref, not_found_ok=True)
        view = client.create_table(view)
        print(f"✓ Created view '{view_ref.table_id}'.")
    except Exception as e:
        print(f"Failed to create view: {e}")

    print("=== BigQuery Asset Creation and Loading Complete! ===")


if __name__ == "__main__":
    create_and_load_assets()

