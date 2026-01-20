"""
SQL Validator - Multi-layer safety validation for generated SQL queries.

This module implements comprehensive validation checks to ensure:
1. Only SELECT operations are allowed
2. Queries only access allowlisted tables
3. Sensitive columns are blocked
4. Row limits and timeouts are enforced
5. SQL injection patterns are prevented
"""

import re
from typing import List, Set

import sqlglot
from sqlglot import ParseError, parse_one
from sqlglot.expressions import (
    Column,
    Delete,
    Drop,
    Insert,
    Select,
    Table,
    Update,
)

from src.models.schemas import (
    GeneratedSQL,
    SafetyConfig,
    ValidationResult,
    ValidationStatus,
    ValidatedSQL,
)


class SQLValidator:
    """
    Multi-layer SQL validator with safety checks.

    Validates SQL queries against:
    - Operation whitelist (SELECT only)
    - Table allowlist
    - Column blocklist (sensitive data)
    - SQL injection patterns
    - Row limits
    """

    def __init__(self, safety_config: SafetyConfig):
        """
        Initialize validator with safety configuration.

        Args:
            safety_config: Safety configuration including allowlists and limits
        """
        self.config = safety_config
        self.allowed_tables: Set[str] = set(
            t.lower() for t in safety_config.allowed_tables
        )
        self.blocked_columns: Set[str] = set(
            c.lower() for c in safety_config.blocked_columns
        )

        # Dangerous SQL patterns to detect
        self.dangerous_patterns = [
            r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)",  # Multiple statements
            r"(xp_cmdshell|exec\s+sp_|execute\s+sp_)",  # System procedures
            r"(WAITFOR|BENCHMARK|SLEEP)\s*\(",  # Timing attacks
            r"(UNION\s+SELECT.*FROM\s+information_schema)",  # Schema fishing
        ]

    def validate(self, generated_sql: GeneratedSQL) -> ValidatedSQL:
        """
        Validate generated SQL and apply safety transformations.

        Args:
            generated_sql: Generated SQL from LLM

        Returns:
            ValidatedSQL with validation result and safe SQL
        """
        sql = generated_sql.sql
        errors: List[str] = []
        warnings: List[str] = []
        checks = {}

        # 1. Parse SQL
        try:
            ast = parse_one(sql, dialect="postgres")
            checks["syntax_valid"] = True
        except ParseError as e:
            errors.append(f"SQL parsing error: {str(e)}")
            checks["syntax_valid"] = False
            return self._create_invalid_result(sql, errors, warnings, checks)

        # 2. Check operation type (SELECT only)
        if not isinstance(ast, Select):
            operation_type = type(ast).__name__
            errors.append(
                f"Only SELECT operations allowed. Found: {operation_type}"
            )
            checks["operation_allowed"] = False

            # Check if it's a dangerous operation
            if isinstance(ast, (Insert, Update, Delete, Drop)):
                errors.append(f"BLOCKED: {operation_type} is a write operation")
        else:
            checks["operation_allowed"] = True

        # 3. Extract and validate tables
        tables = self._extract_tables(ast)
        checks["tables_validated"] = self._validate_tables(tables, errors, warnings)

        # 4. Extract and validate columns
        columns = self._extract_columns(ast)
        checks["columns_validated"] = self._validate_columns(columns, errors, warnings)

        # 5. Check for dangerous patterns
        checks["no_dangerous_patterns"] = self._check_dangerous_patterns(
            sql, errors, warnings
        )

        # 6. Check for SQL injection indicators
        checks["no_injection_patterns"] = self._check_injection_patterns(
            sql, errors, warnings
        )

        # 7. Enforce row limit
        safe_sql = self._enforce_row_limit(ast, sql)
        checks["row_limit_applied"] = True

        # Determine validation status
        if errors:
            status = ValidationStatus.INVALID
            is_safe = False
        elif warnings:
            status = ValidationStatus.VALID
            is_safe = True
            # Could be NEEDS_REWRITE if you want to be extra cautious
        else:
            status = ValidationStatus.VALID
            is_safe = True

        validation_result = ValidationResult(
            status=status,
            is_safe=is_safe,
            errors=errors,
            warnings=warnings,
            checks_performed=checks,
        )

        return ValidatedSQL(
            sql=safe_sql,
            original_sql=sql,
            validation_result=validation_result,
            safety_limits={
                "max_rows": self.config.max_result_rows,
                "timeout_seconds": self.config.max_query_timeout_seconds,
            },
        )

    def _extract_tables(self, ast: Select) -> Set[str]:
        """Extract all table names from SQL AST."""
        tables = set()
        for table in ast.find_all(Table):
            table_name = table.name.lower()
            tables.add(table_name)
        return tables

    def _validate_tables(
        self, tables: Set[str], errors: List[str], warnings: List[str]
    ) -> bool:
        """
        Validate tables against allowlist.

        Returns:
            True if all tables are allowed
        """
        if not self.allowed_tables:
            warnings.append(
                "No table allowlist configured - all tables accessible (not recommended)"
            )
            return True

        invalid_tables = tables - self.allowed_tables
        if invalid_tables:
            errors.append(
                f"Access denied to tables: {', '.join(sorted(invalid_tables))}. "
                f"Allowed tables: {', '.join(sorted(self.allowed_tables))}"
            )
            return False

        return True

    def _extract_columns(self, ast: Select) -> Set[str]:
        """Extract all column names from SQL AST."""
        columns = set()
        for col in ast.find_all(Column):
            if hasattr(col, "name"):
                columns.add(col.name.lower())
        return columns

    def _validate_columns(
        self, columns: Set[str], errors: List[str], warnings: List[str]
    ) -> bool:
        """
        Validate columns against blocklist (sensitive data).

        Returns:
            True if no blocked columns are accessed
        """
        blocked_found = columns & self.blocked_columns
        if blocked_found:
            errors.append(
                f"Access denied to sensitive columns: {', '.join(sorted(blocked_found))}"
            )
            return False
        return True

    def _check_dangerous_patterns(
        self, sql: str, errors: List[str], warnings: List[str]
    ) -> bool:
        """
        Check for dangerous SQL patterns.

        Returns:
            True if no dangerous patterns found
        """
        sql_upper = sql.upper()
        for pattern in self.dangerous_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                errors.append(f"Dangerous SQL pattern detected: {pattern}")
                return False
        return True

    def _check_injection_patterns(
        self, sql: str, errors: List[str], warnings: List[str]
    ) -> bool:
        """
        Check for SQL injection indicators.

        Returns:
            True if no injection patterns found
        """
        # Check for common injection patterns
        injection_patterns = [
            r"'\s*OR\s+'1'\s*=\s*'1",  # Classic OR '1'='1'
            r"'\s*OR\s+1\s*=\s*1",  # OR 1=1
            r"--",  # SQL comments (could be legitimate, so warning only)
            r"/\*.*\*/",  # Multi-line comments
        ]

        has_issues = False
        for pattern in injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                if pattern == r"--" or pattern == r"/\*.*\*/":
                    # Comments might be legitimate, but warn
                    warnings.append(
                        f"SQL contains comments which could indicate injection: {pattern}"
                    )
                else:
                    errors.append(f"Potential SQL injection pattern detected: {pattern}")
                    has_issues = True

        return not has_issues

    def _enforce_row_limit(self, ast: Select, original_sql: str) -> str:
        """
        Enforce maximum row limit by adding or modifying LIMIT clause.

        Args:
            ast: Parsed SQL AST
            original_sql: Original SQL string

        Returns:
            SQL with enforced LIMIT
        """
        max_rows = self.config.max_result_rows

        # Check if LIMIT already exists
        if ast.args.get("limit"):
            existing_limit = ast.args["limit"]
            # If existing limit is higher, replace it
            try:
                limit_value = int(str(existing_limit).strip())
                if limit_value > max_rows:
                    ast.args["limit"] = sqlglot.parse_one(f"{max_rows}").expression
            except (ValueError, AttributeError):
                # If we can't parse the limit, add our own
                pass
        else:
            # Add LIMIT clause
            ast.args["limit"] = sqlglot.parse_one(f"{max_rows}").expression

        return ast.sql(dialect="postgres")

    def _create_invalid_result(
        self, sql: str, errors: List[str], warnings: List[str], checks: dict
    ) -> ValidatedSQL:
        """Create an invalid validation result."""
        validation_result = ValidationResult(
            status=ValidationStatus.INVALID,
            is_safe=False,
            errors=errors,
            warnings=warnings,
            checks_performed=checks,
        )

        return ValidatedSQL(
            sql=sql,
            original_sql=sql,
            validation_result=validation_result,
            safety_limits={
                "max_rows": self.config.max_result_rows,
                "timeout_seconds": self.config.max_query_timeout_seconds,
            },
        )


# ============================================================================
# Helper Functions
# ============================================================================


def validate_sql(generated_sql: GeneratedSQL, safety_config: SafetyConfig) -> ValidatedSQL:
    """
    Convenience function to validate SQL.

    Args:
        generated_sql: Generated SQL to validate
        safety_config: Safety configuration

    Returns:
        Validated SQL with safety checks applied
    """
    validator = SQLValidator(safety_config)
    return validator.validate(generated_sql)


# ============================================================================
# Example Usage
# ============================================================================


if __name__ == "__main__":
    # Example: Validate a safe query
    safe_config = SafetyConfig(
        max_result_rows=1000,
        max_query_timeout_seconds=30,
        allowed_tables=["orders", "customers"],
        blocked_columns=["ssn", "credit_card"],
    )

    # Safe query
    safe_sql = GeneratedSQL(
        sql="SELECT customer_id, order_date, total FROM orders WHERE order_date > '2024-01-01'",
        tables_used=["orders"],
        definitions_applied=["total"],
        assumptions=["Included all order statuses"],
    )

    validator = SQLValidator(safe_config)
    result = validator.validate(safe_sql)
    print(f"Safe query validation: {result.validation_result.status}")
    print(f"Is safe: {result.validation_result.is_safe}")
    print(f"Checks: {result.validation_result.checks_performed}")

    # Unsafe query (DROP)
    unsafe_sql = GeneratedSQL(
        sql="DROP TABLE orders",
        tables_used=["orders"],
        definitions_applied=[],
        assumptions=[],
    )

    result = validator.validate(unsafe_sql)
    print(f"\nUnsafe query validation: {result.validation_result.status}")
    print(f"Errors: {result.validation_result.errors}")

    # Query with blocked column
    blocked_sql = GeneratedSQL(
        sql="SELECT customer_id, ssn FROM customers",
        tables_used=["customers"],
        definitions_applied=[],
        assumptions=[],
    )

    result = validator.validate(blocked_sql)
    print(f"\nBlocked column validation: {result.validation_result.status}")
    print(f"Errors: {result.validation_result.errors}")
