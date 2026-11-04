"""
tests/test_okf_conformance.py
Unit tests verifying OKF v0.2 bundle conformance, YAML frontmatter,
link resolution, and use-case SQL syntax.
"""

import os
import pytest
from scripts.validate_okf import validate_bundle


def test_bundle_conformance():
    bundle_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "okf_bundle")
    # Should run with zero exceptions
    validate_bundle(bundle_dir)


def test_root_index_version():
    bundle_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "okf_bundle")
    root_index = os.path.join(bundle_dir, "index.md")
    assert os.path.exists(root_index)
    with open(root_index, "r", encoding="utf-8") as f:
        content = f.read()
    assert 'okf_version: "0.2"' in content or "okf_version: '0.2'" in content


def test_reserved_files_rules():
    bundle_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "okf_bundle")
    # Subfolder index.md files must NOT have frontmatter
    sub_indexes = [
        os.path.join(bundle_dir, "glossary", "index.md"),
        os.path.join(bundle_dir, "metrics", "index.md"),
        os.path.join(bundle_dir, "conventions", "index.md"),
        os.path.join(bundle_dir, "use-cases", "index.md"),
        os.path.join(bundle_dir, "datasets", "loyalty_poc", "index.md"),
    ]
    for idx_file in sub_indexes:
        if os.path.exists(idx_file):
            with open(idx_file, "r", encoding="utf-8") as f:
                content = f.read()
            assert not content.startswith("---"), f"Sub-index {idx_file} must not have YAML frontmatter."

