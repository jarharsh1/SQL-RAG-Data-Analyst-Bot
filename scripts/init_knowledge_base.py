#!/usr/bin/env python3
"""
Initialize Knowledge Base - Populate vector store with metric definitions,
data dictionary, and example queries.

Usage:
    python scripts/init_knowledge_base.py
"""

import os
import sys
from pathlib import Path

import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.rag import get_rag_retriever


def load_metric_definitions(file_path: str) -> list:
    """Load metric definitions from markdown file."""
    documents = []

    with open(file_path, 'r') as f:
        content = f.read()

    # Simple parser for markdown metric definitions
    # In production, use a proper markdown parser
    sections = content.split('###')

    for section in sections[1:]:  # Skip header
        lines = section.strip().split('\n')
        if not lines:
            continue

        metric_name = lines[0].strip()
        metadata = {}
        text = f"Metric: {metric_name}\n"

        for line in lines[1:]:
            if line.startswith('- **'):
                # Parse metadata
                key_val = line.replace('- **', '').split('**:', 1)
                if len(key_val) == 2:
                    key = key_val[0].strip().lower().replace(' ', '_')
                    val = key_val[1].strip()
                    metadata[key] = val
                    text += f"{key_val[0]}: {val}\n"

        documents.append({
            'text': text,
            'type': 'metric_definition',
            'metadata': {
                'metric_name': metric_name,
                'source': file_path,
                **metadata,
            },
        })

    return documents


def load_data_dictionary(file_path: str) -> list:
    """Load data dictionary from YAML file."""
    documents = []

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    # Process tables
    for table in data.get('tables', []):
        table_name = table['name']
        description = table.get('description', '')
        columns = [col['name'] for col in table.get('columns', [])]

        text = f"Table: {table_name}\nDescription: {description}\nColumns: {', '.join(columns)}"

        # Add foreign keys
        fks = {}
        for fk in table.get('foreign_keys', []):
            fks[fk['column']] = fk['references']

        documents.append({
            'text': text,
            'type': 'table_metadata',
            'metadata': {
                'table_name': table_name,
                'description': description,
                'columns': ','.join(columns),
                'primary_key': table.get('primary_key'),
                'foreign_keys': str(fks) if fks else None,
                'source': file_path,
            },
        })

    # Process business rules
    for rule in data.get('business_rules', []):
        rule_name = rule['name']
        description = rule['description']
        text = f"Business Rule: {rule_name}\n{description}"

        documents.append({
            'text': text,
            'type': 'business_rule',
            'metadata': {
                'rule_name': rule_name,
                'sql_filter': rule.get('sql_filter'),
                'applies_to_tables': ','.join(rule.get('applies_to', [])),
                'source': file_path,
            },
        })

    return documents


def load_example_queries(file_path: str) -> list:
    """Load example SQL queries."""
    documents = []

    with open(file_path, 'r') as f:
        content = f.read()

    # Split by query (look for comment patterns)
    queries = []
    current_query = []

    for line in content.split('\n'):
        if line.startswith('-- Example') and current_query:
            # Save previous query
            query_text = '\n'.join(current_query).strip()
            if query_text and not query_text.startswith('--'):
                queries.append(query_text)
            current_query = [line]
        else:
            current_query.append(line)

    # Add last query
    if current_query:
        query_text = '\n'.join(current_query).strip()
        if query_text and not query_text.startswith('--'):
            queries.append(query_text)

    # Create documents
    for idx, query in enumerate(queries):
        documents.append({
            'text': query,
            'type': 'example_query',
            'metadata': {
                'source': file_path,
                'query_number': idx + 1,
            },
        })

    return documents


def main():
    """Initialize knowledge base."""
    print("Initializing Knowledge Base...")
    print("=" * 60)

    # Get data directory
    data_dir = Path(__file__).parent.parent / 'data' / 'examples'

    # Initialize RAG retriever
    rag = get_rag_retriever()

    # Clear existing collection (optional - comment out to append)
    # rag.collection.delete()
    # rag.collection = rag.client.get_or_create_collection(rag.collection_name)

    total_docs = 0

    # Load metric definitions
    metrics_file = data_dir / 'metric_definitions.md'
    if metrics_file.exists():
        print(f"\nLoading metric definitions from {metrics_file}...")
        metric_docs = load_metric_definitions(str(metrics_file))
        rag.bulk_add_documents(metric_docs)
        print(f"  ✓ Added {len(metric_docs)} metric definitions")
        total_docs += len(metric_docs)
    else:
        print(f"  ✗ Metrics file not found: {metrics_file}")

    # Load data dictionary
    dict_file = data_dir / 'data_dictionary.yaml'
    if dict_file.exists():
        print(f"\nLoading data dictionary from {dict_file}...")
        dict_docs = load_data_dictionary(str(dict_file))
        rag.bulk_add_documents(dict_docs)
        print(f"  ✓ Added {len(dict_docs)} data dictionary entries")
        total_docs += len(dict_docs)
    else:
        print(f"  ✗ Dictionary file not found: {dict_file}")

    # Load example queries
    queries_file = data_dir / 'golden_queries.sql'
    if queries_file.exists():
        print(f"\nLoading example queries from {queries_file}...")
        query_docs = load_example_queries(str(queries_file))
        rag.bulk_add_documents(query_docs)
        print(f"  ✓ Added {len(query_docs)} example queries")
        total_docs += len(query_docs)
    else:
        print(f"  ✗ Queries file not found: {queries_file}")

    print("\n" + "=" * 60)
    print(f"✓ Knowledge base initialized with {total_docs} documents")
    print(f"  Vector store location: {rag.persist_dir}")
    print(f"  Collection name: {rag.collection_name}")


if __name__ == '__main__':
    main()
