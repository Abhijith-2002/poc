"""
tests/test_sql_guard.py
Unit tests for SQL query safety guardrails, AST validation, and cost enforcement.
"""

import pytest
from agent.guardrails import (
    check_bytes_limit,
    mask_email,
    mask_name,
    mask_tabular_data,
    validate_query_guardrails,
)


def test_select_query_permitted():
    sql = "SELECT member_id, total_amount FROM fact_transaction WHERE transaction_date >= '2026-01-01'"
    res = validate_query_guardrails(sql)
    assert res["valid"] is True, f"Expected SELECT query to be valid: {res}"


def test_cte_query_permitted():
    sql = """
    WITH high_spenders AS (
      SELECT member_id, SUM(total_amount) AS spend
      FROM fact_transaction
      GROUP BY member_id
    )
    SELECT * FROM high_spenders WHERE spend > 1000
    """
    res = validate_query_guardrails(sql)
    assert res["valid"] is True, f"Expected CTE query to be valid: {res}"


def test_ddl_drop_blocked():
    sql = "DROP TABLE fact_transaction"
    res = validate_query_guardrails(sql)
    assert res["valid"] is False
    assert "Prohibited" in res["error"] or "Only SELECT" in res["error"]


def test_dml_delete_blocked():
    sql = "DELETE FROM fact_transaction WHERE total_amount < 10"
    res = validate_query_guardrails(sql)
    assert res["valid"] is False
    assert "Prohibited" in res["error"] or "Only SELECT" in res["error"]


def test_dml_update_blocked():
    sql = "UPDATE dim_member SET points_balance = 99999 WHERE member_id = 'M000001'"
    res = validate_query_guardrails(sql)
    assert res["valid"] is False


def test_dml_insert_blocked():
    sql = "INSERT INTO dim_member (member_id) VALUES ('HACKED')"
    res = validate_query_guardrails(sql)
    assert res["valid"] is False


def test_multi_statement_blocked():
    sql = "SELECT 1; DROP TABLE dim_member;"
    res = validate_query_guardrails(sql)
    assert res["valid"] is False
    assert "Multi-statement" in res["error"]


def test_bytes_limit_check():
    under_limit = check_bytes_limit(50_000_000, max_bytes=100_000_000)
    assert under_limit["allowed"] is True

    over_limit = check_bytes_limit(150_000_000, max_bytes=100_000_000)
    assert over_limit["allowed"] is False
    assert "exceeds MAX_BYTES_BILLED" in over_limit["error"]


def test_pii_masking_helpers():
    email = "emma.smith124@gmail.com"
    masked_email = mask_email(email)
    assert masked_email.startswith("e***")
    assert "@" in masked_email
    assert "emma.smith124" not in masked_email

    name = "Emma Smith"
    masked_name = mask_name(name)
    assert "Emma" not in masked_name
    assert "Smith" not in masked_name
    assert masked_name == "E*** S***"


def test_tabular_pii_redaction():
    records = [
        {"member_id": "M0001", "first_name": "Emma", "last_name": "Smith", "email": "emma@gmail.com", "spend": 500.0}
    ]
    # Default masked
    masked = mask_tabular_data(records, show_pii=False)
    assert masked[0]["first_name"] == "E***"
    assert "emma" not in masked[0]["email"]
    assert masked[0]["spend"] == 500.0

    # Unmasked override
    unmasked = mask_tabular_data(records, show_pii=True)
    assert unmasked[0]["first_name"] == "Emma"
    assert unmasked[0]["email"] == "emma@gmail.com"

