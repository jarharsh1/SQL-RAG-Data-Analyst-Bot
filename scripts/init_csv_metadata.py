#!/usr/bin/env python3
"""
CSV Metadata Initializer - Load CSV file metadata into RAG vector store.

This script analyzes CSV files and creates metadata entries that help the
LLM understand what data is available for querying.

Usage:
    python scripts/init_csv_metadata.py
    python scripts/init_csv_metadata.py --csv-dir data/csv
"""

import argparse
import sys
from pathlib import Path

import duckdb

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.rag import get_rag_retriever


def analyze_csv_file(csv_path: Path, connection: duckdb.DuckDBPyConnection) -> dict:
    """
    Analyze a CSV file and extract metadata.

    Args:
        csv_path: Path to CSV file
        connection: DuckDB connection

    Returns:
        Dictionary with table metadata
    """
    table_name = csv_path.stem

    try:
        # Read CSV into temporary view
        connection.execute(f"""
            CREATE OR REPLACE VIEW temp_{table_name} AS
            SELECT * FROM read_csv_auto('{csv_path.absolute()}',
                header=true,
                auto_detect=true
            )
        """)

        # Get column information
        result = connection.execute(f"DESCRIBE temp_{table_name}")
        columns_info = result.fetchall()

        columns = []
        for col in columns_info:
            columns.append({
                "name": col[0],
                "type": str(col[1]),
            })

        # Get row count
        count_result = connection.execute(f"SELECT COUNT(*) FROM temp_{table_name}")
        row_count = count_result.fetchone()[0]

        # Get sample values for each column (first 3 non-null values)
        sample_values = {}
        for col in columns:
            col_name = col["name"]
            try:
                sample_result = connection.execute(f"""
                    SELECT DISTINCT "{col_name}"
                    FROM temp_{table_name}
                    WHERE "{col_name}" IS NOT NULL
                    LIMIT 3
                """)
                samples = [str(row[0]) for row in sample_result.fetchall()]
                sample_values[col_name] = samples
            except Exception:
                sample_values[col_name] = []

        return {
            "table_name": table_name,
            "columns": columns,
            "row_count": row_count,
            "sample_values": sample_values,
            "file_path": str(csv_path),
        }

    except Exception as e:
        print(f"  ✗ Error analyzing {csv_path.name}: {e}")
        return None


def create_table_metadata_doc(metadata: dict) -> dict:
    """
    Create a document for the vector store from table metadata.

    Args:
        metadata: Table metadata dictionary

    Returns:
        Document dictionary for RAG
    """
    table_name = metadata["table_name"]
    columns = metadata["columns"]
    row_count = metadata["row_count"]
    sample_values = metadata["sample_values"]

    # Build descriptive text
    text_parts = [
        f"Table: {table_name}",
        f"Number of rows: {row_count:,}",
        f"",
        "Columns:",
    ]

    for col in columns:
        col_name = col["name"]
        col_type = col["type"]
        samples = sample_values.get(col_name, [])

        col_desc = f"  - {col_name} ({col_type})"
        if samples:
            col_desc += f" - Example values: {', '.join(samples[:3])}"

        text_parts.append(col_desc)

    text = "\n".join(text_parts)

    # Create metadata dict
    doc_metadata = {
        "table_name": table_name,
        "columns": ",".join([c["name"] for c in columns]),
        "row_count": str(row_count),
        "source": metadata["file_path"],
    }

    return {
        "text": text,
        "type": "table_metadata",
        "metadata": doc_metadata,
        "id": f"table_{table_name}",
    }


def create_metric_definitions_from_csv() -> list:
    """
    Create metric definitions based on CSV data.

    Returns:
        List of metric definition documents
    """
    metrics = [
        {
            "name": "Revenue",
            "formula": "SUM(total_amount)",
            "description": "Total revenue from orders",
            "source_table": "orders",
            "filters": "WHERE status = 'completed'",
        },
        {
            "name": "Customer Count",
            "formula": "COUNT(DISTINCT customer_id)",
            "description": "Number of unique customers",
            "source_table": "customers",
            "filters": "WHERE status = 'active'",
        },
        {
            "name": "Order Count",
            "formula": "COUNT(DISTINCT order_id)",
            "description": "Total number of orders",
            "source_table": "orders",
            "filters": "",
        },
        {
            "name": "Units Sold",
            "formula": "SUM(quantity)",
            "description": "Total units sold across all products",
            "source_table": "order_line_items",
            "filters": "",
        },
        {
            "name": "Average Order Value",
            "formula": "AVG(total_amount)",
            "description": "Average revenue per order",
            "source_table": "orders",
            "filters": "WHERE status = 'completed'",
        },
    ]

    documents = []
    for metric in metrics:
        text = f"""Metric: {metric['name']}
Formula: {metric['formula']}
Description: {metric['description']}
Source Table: {metric['source_table']}
Default Filters: {metric['filters'] if metric['filters'] else 'None'}
"""

        doc = {
            "text": text,
            "type": "metric_definition",
            "metadata": {
                "metric_name": metric["name"],
                "formula": metric["formula"],
                "source_table": metric["source_table"],
                "filters": metric["filters"],
                "source": "auto-generated from CSV",
            },
            "id": f"metric_{metric['name'].lower().replace(' ', '_')}",
        }
        documents.append(doc)

    return documents


def main():
    """Load CSV metadata into vector store."""
    parser = argparse.ArgumentParser(description="Initialize CSV metadata in RAG")
    parser.add_argument(
        "--csv-dir",
        default="data/csv",
        help="Directory containing CSV files"
    )

    args = parser.parse_args()

    csv_dir = Path(args.csv_dir)

    if not csv_dir.exists():
        print(f"Error: CSV directory not found: {csv_dir}")
        print("Run: python scripts/generate_sample_data.py first")
        sys.exit(1)

    print("=" * 60)
    print("Initializing CSV Metadata for RAG")
    print("=" * 60)

    # Get RAG retriever
    rag = get_rag_retriever()

    # Create DuckDB connection for analysis
    connection = duckdb.connect(":memory:")

    # Find all CSV files
    csv_files = list(csv_dir.glob("*.csv"))

    if not csv_files:
        print(f"\n✗ No CSV files found in {csv_dir}")
        print("Run: python scripts/generate_sample_data.py first")
        sys.exit(1)

    print(f"\nFound {len(csv_files)} CSV files")

    # Analyze each CSV and create metadata documents
    documents = []

    print("\nAnalyzing CSV files...")
    for csv_file in csv_files:
        print(f"  - {csv_file.name}...")
        metadata = analyze_csv_file(csv_file, connection)

        if metadata:
            doc = create_table_metadata_doc(metadata)
            documents.append(doc)
            print(f"    ✓ {metadata['table_name']}: {metadata['row_count']:,} rows, {len(metadata['columns'])} columns")

    # Add auto-generated metric definitions
    print("\nGenerating metric definitions...")
    metric_docs = create_metric_definitions_from_csv()
    documents.extend(metric_docs)
    print(f"  ✓ Added {len(metric_docs)} metric definitions")

    # Add to vector store
    print("\nAdding to vector store...")
    rag.bulk_add_documents(documents)

    connection.close()

    print("\n" + "=" * 60)
    print(f"✓ CSV metadata initialized with {len(documents)} documents")
    print(f"  - Table metadata: {len(csv_files)}")
    print(f"  - Metric definitions: {len(metric_docs)}")
    print(f"  Vector store location: {rag.persist_dir}")
    print("\nYou can now query your CSV data!")
    print("\nExample questions:")
    print("  - What is the total revenue?")
    print("  - Show me customer count by region")
    print("  - What are the top selling products?")


if __name__ == "__main__":
    main()
