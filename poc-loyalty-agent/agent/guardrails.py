"""
agent/guardrails.py
Security, query safety, cost enforcement, and PII masking guardrails.
"""

import os
import re
from typing import Any, Dict, List
import sqlglot
from sqlglot import exp

MAX_BYTES_BILLED = int(os.getenv("MAX_BYTES_BILLED", "104857600"))  # 100 MB default
SHOW_PII_DEFAULT = os.getenv("SHOW_PII", "false").lower() in ("true", "1", "yes")


def mask_email(email: str) -> str:
    """Masks customer email address: emma.smith@gmail.com -> e***h@g***l.com"""
    if not email or "@" not in email:
        return email
    parts = email.split("@", 1)
    user, domain = parts[0], parts[1]

    # Mask user
    if len(user) <= 2:
        masked_user = user[0] + "***"
    else:
        masked_user = user[0] + "***" + user[-1]

    # Mask domain
    if "." in domain:
        dparts = domain.split(".", 1)
        d_name, d_ext = dparts[0], dparts[1]
        if len(d_name) <= 2:
            masked_domain = d_name[0] + "***." + d_ext
        else:
            masked_domain = d_name[0] + "***" + d_name[-1] + "." + d_ext
    else:
        masked_domain = domain[0] + "***"

    return f"{masked_user}@{masked_domain}"


def mask_name(name: str) -> str:
    """Masks customer name: Emma Smith -> E*** S***"""
    if not name or not isinstance(name, str):
        return name
    tokens = name.strip().split()
    masked_tokens = []
    for t in tokens:
        if len(t) <= 1:
            masked_tokens.append(t)
        else:
            masked_tokens.append(t[0] + "***")
    return " ".join(masked_tokens)


def mask_tabular_data(data: List[Dict[str, Any]], show_pii: bool = False) -> List[Dict[str, Any]]:
    """Applies PII redaction to rows unless show_pii is True."""
    if show_pii or SHOW_PII_DEFAULT:
        return data

    masked_records = []
    pii_name_keys = {"first_name", "last_name", "name", "customer_name", "member_name"}
    pii_email_keys = {"email", "email_address"}

    for row in data:
        new_row = {}
        for k, v in row.items():
            k_lower = k.lower()
            if k_lower in pii_email_keys and isinstance(v, str):
                new_row[k] = mask_email(v)
            elif k_lower in pii_name_keys and isinstance(v, str):
                new_row[k] = mask_name(v)
            else:
                new_row[k] = v
        masked_records.append(new_row)
    return masked_records


def validate_query_guardrails(sql: str) -> Dict[str, Any]:
    """
    Validates that a SQL query is strictly read-only:
      - Rejects multiple statements (semicolons).
      - Rejects DDL (CREATE, DROP, ALTER) and DML (INSERT, UPDATE, DELETE, MERGE).
      - Requires SELECT or WITH as the root AST expression.
    """
    # Check for multiple statements
    stripped = sql.strip()
    if stripped.endswith(";"):
        stripped = stripped[:-1].strip()
    if ";" in stripped:
        return {
            "valid": False,
            "error": "Query rejected: Multi-statement queries are strictly prohibited."
        }

    # AST check
    try:
        parsed = sqlglot.parse_one(sql, read="bigquery")
    except Exception as e:
        return {
            "valid": False,
            "error": f"SQL syntax error: {str(e)}"
        }

    if not isinstance(parsed, (exp.Select, exp.Union)):
        return {
            "valid": False,
            "error": f"Query rejected: Prohibited statement type '{type(parsed).__name__}'. Only SELECT and WITH statements are allowed."
        }

    prohibited = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Alter,
        exp.Create,
        exp.Merge,
        exp.Command,
    )
    for node in parsed.walk():
        if isinstance(node, prohibited):
            return {
                "valid": False,
                "error": f"Query rejected: Prohibited clause '{type(node).__name__}' detected."
            }

    return {"valid": True, "parsed": parsed}


def check_bytes_limit(total_bytes_processed: int, max_bytes: int = MAX_BYTES_BILLED) -> Dict[str, Any]:
    """Ensures dry-run byte estimate does not exceed MAX_BYTES_BILLED."""
    if total_bytes_processed > max_bytes:
        return {
            "allowed": False,
            "error": f"Query aborted: Estimated bytes ({total_bytes_processed:,} bytes) exceeds MAX_BYTES_BILLED limit ({max_bytes:,} bytes). Ask user for approval.",
            "estimated_bytes": total_bytes_processed,
            "max_bytes": max_bytes,
        }
    return {
        "allowed": True,
        "estimated_bytes": total_bytes_processed,
        "max_bytes": max_bytes,
    }

