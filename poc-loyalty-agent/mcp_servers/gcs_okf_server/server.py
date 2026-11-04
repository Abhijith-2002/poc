#!/usr/bin/env python3
"""
mcp_servers/gcs_okf_server/server.py
Minimal, zero-trust, read-only FastMCP server for accessing OKF v0.2 bundle concepts.
Exposes ONLY:
  - list_objects(prefix: str) -> list[str]
  - read_object(path: str) -> str
  - read_objects_batch(paths: list[str]) -> dict[str, str]
"""

import os
import sys
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT")
BUCKET_NAME = os.getenv("OKF_BUCKET")
OKF_PREFIX = os.getenv("OKF_PREFIX", "okf_bundle").strip("/")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOCAL_BUNDLE_DIR = os.getenv("LOCAL_BUNDLE_DIR", os.path.join(REPO_ROOT, "okf_bundle"))

mcp = FastMCP("GCS-OKF-Server")

# Check if live GCS is available
_gcs_bucket = None
if BUCKET_NAME and BUCKET_NAME != "your-gcs-bucket-name":
    try:
        from google.cloud import storage
        client = storage.Client(project=PROJECT_ID)
        _gcs_bucket = client.bucket(BUCKET_NAME)
        # Test access
        _gcs_bucket.exists()
    except Exception as e:
        _gcs_bucket = None


@mcp.tool()
def list_objects(prefix: str = "") -> list[str]:
    """
    Lists object keys/paths within the OKF bundle in Cloud Storage.
    
    Args:
        prefix: Optional path prefix to filter objects (e.g. 'use-cases/', 'datasets/').
    """
    clean_prefix = prefix.lstrip("/")
    if _gcs_bucket is not None:
        full_prefix = f"{OKF_PREFIX}/{clean_prefix}" if OKF_PREFIX else clean_prefix
        blobs = _gcs_bucket.list_blobs(prefix=full_prefix)
        keys = []
        for b in blobs:
            name = b.name
            if OKF_PREFIX and name.startswith(OKF_PREFIX + "/"):
                name = name[len(OKF_PREFIX) + 1:]
            keys.append(name)
        return sorted(keys)

    # Local fallback
    base_dir = os.path.abspath(LOCAL_BUNDLE_DIR)
    results = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.startswith("."):
                continue
            full_path = os.path.join(root, f)
            rel = os.path.relpath(full_path, base_dir)
            if not clean_prefix or rel.startswith(clean_prefix):
                results.append(rel)
    return sorted(results)


@mcp.tool()
def read_object(path: str) -> str:
    """
    Reads the full UTF-8 text content of a single OKF concept Markdown document.
    
    Args:
        path: Path of the concept within the bundle (e.g. 'index.md', 'use-cases/uc01-top-members-doncaster-email.md').
    """
    clean_path = path.lstrip("/")
    # Security: block path traversal
    if ".." in clean_path:
        raise ValueError("Invalid path: directory traversal prohibited.")

    if _gcs_bucket is not None:
        full_name = f"{OKF_PREFIX}/{clean_path}" if OKF_PREFIX else clean_path
        blob = _gcs_bucket.blob(full_name)
        if not blob.exists():
            raise FileNotFoundError(f"Object not found in GCS: gs://{BUCKET_NAME}/{full_name}")
        return blob.download_as_text(encoding="utf-8")

    # Local fallback
    base_dir = os.path.abspath(LOCAL_BUNDLE_DIR)
    local_path = os.path.normpath(os.path.join(base_dir, clean_path))
    if not local_path.startswith(base_dir) or not os.path.isfile(local_path):
        raise FileNotFoundError(f"Bundle object not found: {clean_path}")

    with open(local_path, "r", encoding="utf-8") as f:
        return f.read()


@mcp.tool()
def read_objects_batch(paths: list[str]) -> dict[str, str]:
    """
    Reads multiple OKF concept documents in a single round-trip.
    
    Args:
        paths: List of concept paths to read.
    """
    results = {}
    for p in paths:
        try:
            results[p] = read_object(p)
        except Exception as e:
            results[p] = f"ERROR: {str(e)}"
    return results


if __name__ == "__main__":
    mcp.run()
