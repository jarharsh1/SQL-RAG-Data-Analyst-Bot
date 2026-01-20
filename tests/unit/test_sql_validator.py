"""
Unit tests for SQL Validator.
"""

import pytest

from src.core.sql_validator import SQLValidator
from src.models.schemas import GeneratedSQL, SafetyConfig, ValidationStatus


class TestSQLValidator:
    """Test cases for SQL validator."""

    @pytest.fixture
    def validator(self):
        """Create validator with test config."""
        config = SafetyConfig(
            max_result_rows=1000,
            max_query_timeout_seconds=30,
            allowed_tables=["orders", "customers", "products"],
            blocked_columns=["ssn", "credit_card", "password"],
        )
        return SQLValidator(config)

    def test_validate_safe_query(self, validator):
        """Test validation of a safe SELECT query."""
        sql = GeneratedSQL(
            sql="SELECT customer_id, order_date FROM orders WHERE order_date > '2024-01-01'",
            tables_used=["orders"],
            definitions_applied=[],
            assumptions=[],
        )

        result = validator.validate(sql)
        assert result.validation_result.is_safe
        assert result.validation_result.status == ValidationStatus.VALID
        assert len(result.validation_result.errors) == 0

    def test_validate_drop_table(self, validator):
        """Test that DROP TABLE is blocked."""
        sql = GeneratedSQL(
            sql="DROP TABLE orders",
            tables_used=["orders"],
            definitions_applied=[],
            assumptions=[],
        )

        result = validator.validate(sql)
        assert not result.validation_result.is_safe
        assert result.validation_result.status == ValidationStatus.INVALID
        assert any("SELECT" in err for err in result.validation_result.errors)

    def test_validate_blocked_table(self, validator):
        """Test that non-allowlisted tables are blocked."""
        sql = GeneratedSQL(
            sql="SELECT * FROM users",
            tables_used=["users"],
            definitions_applied=[],
            assumptions=[],
        )

        result = validator.validate(sql)
        assert not result.validation_result.is_safe
        assert any("Access denied to tables" in err for err in result.validation_result.errors)

    def test_validate_blocked_column(self, validator):
        """Test that sensitive columns are blocked."""
        sql = GeneratedSQL(
            sql="SELECT customer_id, ssn FROM customers",
            tables_used=["customers"],
            definitions_applied=[],
            assumptions=[],
        )

        result = validator.validate(sql)
        assert not result.validation_result.is_safe
        assert any("sensitive columns" in err for err in result.validation_result.errors)

    def test_enforce_row_limit(self, validator):
        """Test that row limit is enforced."""
        sql = GeneratedSQL(
            sql="SELECT * FROM orders",
            tables_used=["orders"],
            definitions_applied=[],
            assumptions=[],
        )

        result = validator.validate(sql)
        assert "LIMIT" in result.sql
        assert "1000" in result.sql

    def test_row_limit_not_exceeded(self, validator):
        """Test that existing LIMIT is not increased."""
        sql = GeneratedSQL(
            sql="SELECT * FROM orders LIMIT 100",
            tables_used=["orders"],
            definitions_applied=[],
            assumptions=[],
        )

        result = validator.validate(sql)
        assert result.validation_result.is_safe
        # Should keep the existing LIMIT 100
        assert "LIMIT" in result.sql


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
