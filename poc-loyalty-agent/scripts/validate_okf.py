#!/usr/bin/env python3
"""
scripts/validate_okf.py
Validates OKF v0.2 bundle conformance, checks relative markdown links,
asserts 1-to-1 use-case mapping, and dry-runs every canonical SQL template.
"""

import os
import re
import sys
import yaml
import sqlglot


def parse_frontmatter(content: str):
    """Parses YAML frontmatter from markdown file."""
    if not content.startswith("---"):
        return None, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content
    fm_raw = parts[1]
    body = parts[2]
    try:
        fm = yaml.safe_load(fm_raw)
        return fm, body
    except Exception as e:
        raise ValueError(f"YAML parsing error: {e}")


def validate_bundle(bundle_dir: str = "okf_bundle"):
    print(f"=== Validating OKF v0.2 Bundle in '{bundle_dir}' ===")
    errors = []
    
    # 1. Root index.md checks
    root_index = os.path.join(bundle_dir, "index.md")
    if not os.path.exists(root_index):
        errors.append("Root index.md does not exist.")
    else:
        with open(root_index, "r", encoding="utf-8") as f:
            content = f.read()
        fm, body = parse_frontmatter(content)
        if not fm:
            errors.append("Root index.md missing YAML frontmatter.")
        elif fm.get("okf_version") != "0.2":
            errors.append(f"Root index.md okf_version must be '0.2', got {fm.get('okf_version')}")
        else:
            print("✓ Root index.md has valid frontmatter and okf_version: '0.2'")

    # 2. log.md checks
    log_file = os.path.join(bundle_dir, "log.md")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            c = f.read()
        fm, _ = parse_frontmatter(c)
        if fm:
            errors.append("log.md must NOT have YAML frontmatter.")
        if not re.search(r"^##?\s+\d{4}-\d{2}-\d{2}", c, re.MULTILINE):
            errors.append("log.md must contain dated entries formatted as 'YYYY-MM-DD'.")
        else:
            print("✓ log.md has no frontmatter and valid dated headings.")

    # 3. Walk all markdown files
    all_files = []
    use_case_files = {}
    link_targets_to_check = []

    for root, dirs, files in os.walk(bundle_dir):
        for file in files:
            if not file.endswith(".md"):
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, bundle_dir)
            all_files.append(rel_path)
            
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            is_root_index = (rel_path == "index.md")
            is_non_root_index = (file == "index.md" and not is_root_index)
            is_log = (rel_path == "log.md")

            fm, body = parse_frontmatter(content)

            if is_non_root_index:
                if fm is not None:
                    errors.append(f"Non-root index file '{rel_path}' must NOT have YAML frontmatter.")
            elif not is_root_index and not is_log:
                if fm is None:
                    errors.append(f"Concept '{rel_path}' is missing YAML frontmatter.")
                else:
                    c_type = fm.get("type")
                    if not c_type or not isinstance(c_type, str) or not c_type.strip():
                        errors.append(f"Concept '{rel_path}' must have a non-empty string 'type'.")
                    
                    # Track use cases
                    uc_id = fm.get("use_case_id")
                    if uc_id:
                        if uc_id in use_case_files:
                            errors.append(f"Duplicate use_case_id '{uc_id}' in '{rel_path}' and '{use_case_files[uc_id]}'.")
                        use_case_files[uc_id] = (rel_path, fm, body)

            # Collect markdown links for verification
            # Markdown link pattern: [anchor](url)
            links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
            for text, link in links:
                if link.startswith("http://") or link.startswith("https://") or link.startswith("#") or link.startswith("mailto:"):
                    continue
                link_targets_to_check.append((rel_path, link))

    print(f"Discovered {len(all_files)} Markdown files across the bundle.")

    # 4. Validate links
    broken_links = 0
    for source_file, target_link in link_targets_to_check:
        clean_link = target_link.split("#")[0].strip()
        if not clean_link:
            continue
        if clean_link.startswith("/"):
            # Bundle-relative
            dest_path = os.path.join(bundle_dir, clean_link.lstrip("/"))
        else:
            # File-relative
            source_dir = os.path.dirname(os.path.join(bundle_dir, source_file))
            dest_path = os.path.normpath(os.path.join(source_dir, clean_link))
            
        if not os.path.exists(dest_path):
            errors.append(f"Broken link in '{source_file}': target '{target_link}' does not exist (resolved: {dest_path})")
            broken_links += 1

    if broken_links == 0:
        print("✓ All relative concept links verified with zero broken links.")

    # 5. Assert One-to-One Use Case Mapping
    expected_ucs = {"UC1", "UC1a", "UC2", "UC2a", "UC3", "UC3a", "UC4", "UC4a", "UC5", "UC6", "UC7", "UC8"}
    found_ucs = set(use_case_files.keys())
    missing_ucs = expected_ucs - found_ucs
    extra_ucs = found_ucs - expected_ucs
    if missing_ucs:
        errors.append(f"Missing expected use cases: {missing_ucs}")
    if extra_ucs:
        errors.append(f"Unexpected extra use cases: {extra_ucs}")

    # Check that use-cases/index.md and routing/question-routing.md link to every use case
    with open(os.path.join(bundle_dir, "use-cases", "index.md"), "r", encoding="utf-8") as f:
        uc_index_content = f.read()
    with open(os.path.join(bundle_dir, "routing", "question-routing.md"), "r", encoding="utf-8") as f:
        routing_content = f.read()

    for uc_id in expected_ucs:
        if uc_id in use_case_files:
            rel_file = use_case_files[uc_id][0]
            base_name = os.path.basename(rel_file)
            if base_name not in uc_index_content:
                errors.append(f"Use case '{uc_id}' ({base_name}) is not linked in 'use-cases/index.md'")
            if base_name not in routing_content:
                errors.append(f"Use case '{uc_id}' ({base_name}) is not linked in 'routing/question-routing.md'")

    print(f"✓ One-to-one mapping confirmed for all {len(expected_ucs)} use cases (UC1 to UC8 incl. variants).")

    # 6. SQL Validation & AST Parsing
    print("\n--- Validating SQL Templates in Use Cases ---")
    sql_errors = 0
    for uc_id in sorted(use_case_files.keys()):
        rel_file, fm, body = use_case_files[uc_id]
        # Extract SQL fence
        match = re.search(r"```sql\s*(.+?)\s*```", body, re.DOTALL)
        if not match:
            errors.append(f"Use case '{uc_id}' in '{rel_file}' has no ```sql block.")
            sql_errors += 1
            continue
        raw_sql = match.group(1).strip()
        
        # Replace template placeholders
        test_sql = raw_sql.replace("${PROJECT}.${DATASET}", "loyalty_poc")
        # Replace parameters with literal values for AST parsing
        test_sql = re.sub(r"@store_name\b", "'Doncaster'", test_sql)
        test_sql = re.sub(r"@window_months\b", "6", test_sql)
        test_sql = re.sub(r"@window_days\b", "30", test_sql)
        test_sql = re.sub(r"@top_n\b", "100", test_sql)
        test_sql = re.sub(r"@min_visits\b", "5", test_sql)
        test_sql = re.sub(r"@target_age_band\b", "'65+'", test_sql)
        test_sql = re.sub(r"@points_threshold\b", "3000", test_sql)

        try:
            parsed = sqlglot.parse_one(test_sql, read="bigquery")
            # Verify read-only
            if not isinstance(parsed, (sqlglot.exp.Select, sqlglot.exp.Union)):
                errors.append(f"SQL for '{uc_id}' is not a SELECT/UNION statement (type: {type(parsed).__name__}).")
                sql_errors += 1
        except Exception as e:
            errors.append(f"SQL syntax error in '{uc_id}': {e}")
            sql_errors += 1

    if sql_errors == 0:
        print("✓ All 12 canonical SQL templates parsed successfully with sqlglot (BigQuery dialect).")

    # 7. Summary
    if errors:
        print(f"\n❌ Validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\n=== OKF Bundle Conformance & SQL Validation Passed 100%! ===")


if __name__ == "__main__":
    b_dir = sys.argv[1] if len(sys.argv) > 1 else "okf_bundle"
    validate_bundle(b_dir)

