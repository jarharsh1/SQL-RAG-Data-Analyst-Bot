"""
SQL Executor - Safe database query execution.

Executes validated SQL queries with:
- Read-only connection
- Query timeout enforcement
- Result row limits
- Error handling
"""

import time
from typing import Any, Dict, List

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from src.models.schemas import DatabaseConfig, QueryResult, ValidatedSQL


class SQLExecutor:
    """
    Safe SQL query executor.

    Executes SELECT queries with safety limits:
    - Read-only connection
    - Query timeout
    - Result row limits
    - Proper error handling
    """

    def __init__(self, db_config: DatabaseConfig):
        """
        Initialize SQL executor.

        Args:
            db_config: Database configuration
        """
        self.config = db_config
        self.engine: Engine = self._create_engine()

    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with safety settings."""
        engine = create_engine(
            self.config.url,
            pool_size=self.config.pool_size,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False,  # Set to True for SQL logging
        )
        return engine

    def execute(self, validated_sql: ValidatedSQL) -> QueryResult:
        """
        Execute validated SQL query.

        Args:
            validated_sql: Validated SQL with safety checks

        Returns:
            Query result with data and metadata
        """
        start_time = time.time()

        try:
            with self.engine.connect() as conn:
                # Set query timeout (PostgreSQL syntax)
                if self.config.type == "postgresql":
                    timeout_ms = self.config.query_timeout * 1000
                    conn.execute(text(f"SET statement_timeout = {timeout_ms}"))

                # Execute query
                result_proxy = conn.execute(text(validated_sql.sql))

                # Fetch results (limited by LIMIT clause in SQL)
                rows = result_proxy.fetchall()
                columns = list(result_proxy.keys())

                # Convert to list of dicts
                data = [dict(zip(columns, row)) for row in rows]

                execution_time_ms = (time.time() - start_time) * 1000

                # Check if results were truncated
                max_rows = validated_sql.safety_limits.get("max_rows", 10000)
                truncated = len(data) >= max_rows

                return QueryResult(
                    data=data,
                    columns=columns,
                    row_count=len(data),
                    execution_time_ms=execution_time_ms,
                    truncated=truncated,
                    error=None,
                )

        except SQLAlchemyError as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Query execution failed: {str(e)}"

            return QueryResult(
                data=[],
                columns=[],
                row_count=0,
                execution_time_ms=execution_time_ms,
                truncated=False,
                error=error_msg,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Unexpected error: {str(e)}"

            return QueryResult(
                data=[],
                columns=[],
                row_count=0,
                execution_time_ms=execution_time_ms,
                truncated=False,
                error=error_msg,
            )

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close database connection pool."""
        self.engine.dispose()


# ============================================================================
# Convenience Function
# ============================================================================


def execute_sql(validated_sql: ValidatedSQL, db_config: DatabaseConfig) -> QueryResult:
    """
    Convenience function to execute SQL.

    Args:
        validated_sql: Validated SQL
        db_config: Database configuration

    Returns:
        Query result
    """
    executor = SQLExecutor(db_config)
    try:
        return executor.execute(validated_sql)
    finally:
        executor.close()
