#!/usr/bin/env python3
"""
scripts/upload_to_gcs.py
Uploads the local OKF v0.2 bundle to Google Cloud Storage (gs://$OKF_BUCKET/$OKF_PREFIX).
Prints the bundle GCS URI and a complete object listing.
Uses the Cloud Storage SDK (allowed ONLY in one-off setup scripts).
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT")
BUCKET_NAME = os.getenv("OKF_BUCKET")
PREFIX = os.getenv("OKF_PREFIX", "okf_bundle").strip("/")
LOCAL_BUNDLE_DIR = os.getenv("LOCAL_BUNDLE_DIR", "okf_bundle")


def upload_bundle():
    print(f"=== Uploading OKF v0.2 Bundle to GCS ===")
    
    if not BUCKET_NAME or BUCKET_NAME == "your-gcs-bucket-name":
        print("⚠️ Warning: OKF_BUCKET is not set or set to placeholder in .env.")
        print("Please configure OKF_BUCKET in .env before uploading to live GCS.")
        print(f"Local bundle remains available in '{LOCAL_BUNDLE_DIR}' for local MCP serving.")
        return

    try:
        from google.cloud import storage
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(BUCKET_NAME)
    except Exception as e:
        print(f"Failed to initialize Cloud Storage client: {e}")
        return

    print(f"Target GCS URI: gs://{BUCKET_NAME}/{PREFIX}/")
    uploaded_files = []

    for root, dirs, files in os.walk(LOCAL_BUNDLE_DIR):
        for file in files:
            if file.startswith("."):
                continue
            local_path = os.path.join(root, file)
            rel_path = os.path.relpath(local_path, LOCAL_BUNDLE_DIR)
            gcs_blob_name = f"{PREFIX}/{rel_path}" if PREFIX else rel_path
            
            blob = bucket.blob(gcs_blob_name)
            blob.upload_from_filename(local_path, content_type="text/markdown; charset=utf-8")
            uploaded_files.append((gcs_blob_name, os.path.getsize(local_path)))

    print(f"\n✓ Successfully uploaded {len(uploaded_files)} objects to gs://{BUCKET_NAME}/{PREFIX}/:")
    for blob_name, size in sorted(uploaded_files):
        print(f"  - gs://{BUCKET_NAME}/{blob_name} ({size:,} bytes)")

    print(f"\nBundle Root URI: gs://{BUCKET_NAME}/{PREFIX}/index.md")


if __name__ == "__main__":
    upload_bundle()

