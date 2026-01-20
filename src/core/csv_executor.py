"""
CSV Executor - Query CSV files using DuckDB (in-memory SQL database).

This allows the system to work without a traditional database by querying
CSV files directly using SQL. Perfect for demos and testing.
"""

import time
from pathlib import Path
from typing import Any, Dict, List

import duckdb

from src.models.schemas import QueryResult, ValidatedSQL


class CSVExecutor:
    """
    Execute SQL queries on CSV files using DuckDB.

    DuckDB is an in-memory analytical database that can query CSV files
    directly without loading them into a traditional database.
    """

    def __init__(self, csv_dir: str = "./data/csv"):
        """
        Initialize CSV executor.

        Args:
            csv_dir: Directory containing CSV files
        """
        self.csv_dir = Path(csv_dir)
        self.connection = duckdb.connect(":memory:")

        # Register CSV files as tables
        self._register_csv_tables()

    def _register_csv_tables(self) -> None:
        """Register all CSV files in the directory as DuckDB tables."""
        if not self.csv_dir.exists():
            print(f"Warning: CSV directory not found: {self.csv_dir}")
            return

        csv_files = list(self.csv_dir.glob("*.csv"))

        if not csv_files:
            print(f"Warning: No CSV files found in {self.csv_dir}")
            return

        for csv_file in csv_files:
            table_name = csv_file.stem  # Filename without extension

            # Create view that reads from CSV
            # DuckDB can read CSV files directly
            create_view_sql = f"""
            CREATE OR REPLACE VIEW {table_name} AS
            SELECT * FROM read_csv_auto('{csv_file.absolute()}',
                header=true,
                auto_detect=true
            )
            """

            try:
                self.connection.execute(create_view_sql)
                print(f"✓ Registered CSV table: {table_name}")
            except Exception as e:
                print(f"✗ Failed to register {table_name}: {e}")

    def execute(self, validated_sql: ValidatedSQL) -> QueryResult:
        """
        Execute validated SQL query on CSV files.

        Args:
            validated_sql: Validated SQL with safety checks

        Returns:
            Query result with data and metadata
        """
        start_time = time.time()

        try:
            # Execute query
            result = self.connection.execute(validated_sql.sql)

            # Fetch results
            rows = result.fetchall()
            columns = [desc[0] for desc in result.description] if result.description else []

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

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"CSV query execution failed: {str(e)}"

            return QueryResult(
                data=[],
                columns=[],
                row_count=0,
                execution_time_ms=execution_time_ms,
                truncated=False,
                error=error_msg,
            )

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a CSV table.

        Args:
            table_name: Name of the table (CSV filename without extension)

        Returns:
            Dictionary with table info (columns, types, row count)
        """
        try:
            # Get column information
            result = self.connection.execute(f"DESCRIBE {table_name}")
            columns_info = result.fetchall()

            columns = []
            for col in columns_info:
                columns.append({
                    "name": col[0],
                    "type": col[1],
                })

            # Get row count
            count_result = self.connection.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = count_result.fetchone()[0]

            return {
                "table_name": table_name,
                "columns": columns,
                "row_count": row_count,
            }

        except Exception as e:
            return {
                "table_name": table_name,
                "error": str(e),
            }

    def list_tables(self) -> List[str]:
        """List all available CSV tables."""
        try:
            result = self.connection.execute("SHOW TABLES")
            tables = [row[0] for row in result.fetchall()]
            return tables
        except Exception:
            return []

    def test_connection(self) -> bool:
        """
        Test CSV executor connection.

        Returns:
            True if connection is working
        """
        try:
            self.connection.execute("SELECT 1")
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close DuckDB connection."""
        self.connection.close()


# ============================================================================
# Convenience Function
# ============================================================================


def execute_csv_query(validated_sql: ValidatedSQL, csv_dir: str = "./data/csv") -> QueryResult:
    """
    Convenience function to execute SQL on CSV files.

    Args:
        validated_sql: Validated SQL
        csv_dir: Directory containing CSV files

    Returns:
        Query result
    """
    executor = CSVExecutor(csv_dir)
    try:
        return executor.execute(validated_sql)
    finally:
        executor.close()


# ============================================================================
# Example Usage
# ============================================================================


if __name__ == "__main__":
    # Example: Query CSV files
    print("CSV Executor Test")
    print("=" * 60)

    executor = CSVExecutor("./data/csv")

    # List tables
    print("\nAvailable tables:")
    for table in executor.list_tables():
        info = executor.get_table_info(table)
        print(f"  - {table}: {info.get('row_count', 'N/A')} rows")

    # Test query
    from src.models.schemas import GeneratedSQL, SafetyConfig
    from src.core.sql_validator import SQLValidator

    config = SafetyConfig(
        max_result_rows=10,
        max_query_timeout_seconds=30,
        allowed_tables=["customers", "orders", "products"],
        blocked_columns=[],
    )

    validator = SQLValidator(config)

    # Generate sample query
    gen_sql = GeneratedSQL(
        sql="SELECT region, COUNT(*) as customer_count FROM customers GROUP BY region ORDER BY customer_count DESC",
        tables_used=["customers"],
        definitions_applied=[],
        assumptions=[],
    )

    validated = validator.validate(gen_sql)

    if validated.validation_result.is_safe:
        result = executor.execute(validated)
        print(f"\nQuery: {validated.sql}")
        print(f"Results: {result.row_count} rows in {result.execution_time_ms:.0f}ms")

        if result.data:
            print("\nData:")
            for row in result.data:
                print(f"  {row}")
    else:
        print(f"Validation failed: {validated.validation_result.errors}")

    executor.close()
