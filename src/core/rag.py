"""
RAG (Retrieval-Augmented Generation) System.

Retrieves relevant context from vector store:
- Metric definitions
- Data dictionary (tables, columns, relationships)
- Business rules and exclusions
- Example "golden" queries

Uses ChromaDB for vector storage and semantic search.
"""

from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_openai import OpenAIEmbeddings

from src.models.schemas import (
    BusinessRule,
    Citation,
    MetricDefinition,
    ParsedQuestion,
    RetrievedContext,
    TableMetadata,
)


class RAGRetriever:
    """
    RAG retrieval system using ChromaDB.

    Performs semantic search over knowledge base to retrieve:
    - Metric definitions
    - Table/column metadata
    - Business rules
    - Example queries
    """

    def __init__(
        self,
        persist_dir: str = "./data/vector_store",
        collection_name: str = "data_dictionary",
        embedding_model: str = "text-embedding-3-small",
    ):
        """
        Initialize RAG retriever.

        Args:
            persist_dir: Directory for ChromaDB persistence
            collection_name: Name of the ChromaDB collection
            embedding_model: OpenAI embedding model name
        """
        self.persist_dir = persist_dir
        self.collection_name = collection_name

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model=embedding_model)

    def retrieve(self, parsed_question: ParsedQuestion, top_k: int = 5) -> RetrievedContext:
        """
        Retrieve relevant context for a parsed question.

        Args:
            parsed_question: Parsed user question
            top_k: Number of results to retrieve per query

        Returns:
            Retrieved context with citations
        """
        # Build search query
        search_query = self._build_search_query(parsed_question)

        # Search for relevant documents
        results = self.collection.query(
            query_texts=[search_query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # Parse results into structured context
        return self._parse_results(results, parsed_question)

    def _build_search_query(self, parsed_question: ParsedQuestion) -> str:
        """
        Build semantic search query from parsed question.

        Args:
            parsed_question: Parsed question

        Returns:
            Search query string
        """
        parts = [parsed_question.original_question]

        if parsed_question.metrics:
            parts.append(f"Metrics: {', '.join(parsed_question.metrics)}")

        if parsed_question.dimensions:
            parts.append(f"Dimensions: {', '.join(parsed_question.dimensions)}")

        return " ".join(parts)

    def _parse_results(
        self, results: dict, parsed_question: ParsedQuestion
    ) -> RetrievedContext:
        """
        Parse ChromaDB results into RetrievedContext.

        Args:
            results: ChromaDB query results
            parsed_question: Original parsed question

        Returns:
            Structured retrieved context
        """
        metric_definitions = []
        table_metadata = []
        business_rules = []
        example_queries = []
        citations = []

        # Extract results
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, metadata, distance in zip(documents, metadatas, distances):
            # Calculate relevance score (1 - cosine distance)
            relevance_score = 1 - distance

            # Create citation
            citation = Citation(
                source=metadata.get("source", "unknown"),
                location=metadata.get("location"),
                content=doc[:200] + "..." if len(doc) > 200 else doc,
                relevance_score=relevance_score,
            )
            citations.append(citation)

            # Parse based on document type
            doc_type = metadata.get("type", "unknown")

            if doc_type == "metric_definition":
                metric = self._parse_metric_definition(doc, metadata, citation)
                if metric:
                    metric_definitions.append(metric)

            elif doc_type == "table_metadata":
                table = self._parse_table_metadata(doc, metadata)
                if table:
                    table_metadata.append(table)

            elif doc_type == "business_rule":
                rule = self._parse_business_rule(doc, metadata)
                if rule:
                    business_rules.append(rule)

            elif doc_type == "example_query":
                example_queries.append(doc)

        return RetrievedContext(
            metric_definitions=metric_definitions,
            table_metadata=table_metadata,
            business_rules=business_rules,
            example_queries=example_queries,
            citations=citations,
        )

    def _parse_metric_definition(
        self, doc: str, metadata: dict, citation: Citation
    ) -> Optional[MetricDefinition]:
        """Parse metric definition from document."""
        try:
            return MetricDefinition(
                name=metadata.get("metric_name", "unknown"),
                formula=metadata.get("formula", doc),
                source_table=metadata.get("source_table", "unknown"),
                grain=metadata.get("grain", "row"),
                filters=metadata.get("filters", "").split(",") if metadata.get("filters") else [],
                citation=citation,
            )
        except Exception:
            return None

    def _parse_table_metadata(self, doc: str, metadata: dict) -> Optional[TableMetadata]:
        """Parse table metadata from document."""
        try:
            return TableMetadata(
                table_name=metadata.get("table_name", "unknown"),
                columns=metadata.get("columns", "").split(",") if metadata.get("columns") else [],
                primary_key=metadata.get("primary_key"),
                foreign_keys=(
                    eval(metadata.get("foreign_keys", "{}"))
                    if metadata.get("foreign_keys")
                    else {}
                ),
                description=metadata.get("description", doc),
            )
        except Exception:
            return None

    def _parse_business_rule(self, doc: str, metadata: dict) -> Optional[BusinessRule]:
        """Parse business rule from document."""
        try:
            return BusinessRule(
                name=metadata.get("rule_name", "unknown"),
                description=doc,
                sql_filter=metadata.get("sql_filter"),
                applies_to_tables=(
                    metadata.get("applies_to_tables", "").split(",")
                    if metadata.get("applies_to_tables")
                    else []
                ),
            )
        except Exception:
            return None

    def add_document(
        self,
        text: str,
        doc_type: str,
        metadata: dict,
        doc_id: Optional[str] = None,
    ) -> str:
        """
        Add a document to the vector store.

        Args:
            text: Document text
            doc_type: Type (metric_definition, table_metadata, etc.)
            metadata: Additional metadata
            doc_id: Optional document ID

        Returns:
            Document ID
        """
        # Generate embedding
        embedding = self.embeddings.embed_query(text)

        # Generate ID if not provided
        if doc_id is None:
            doc_id = f"{doc_type}_{len(self.collection.get()['ids'])}"

        # Add metadata
        full_metadata = {"type": doc_type, **metadata}

        # Add to collection
        self.collection.add(
            ids=[doc_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[full_metadata],
        )

        return doc_id

    def bulk_add_documents(self, documents: List[dict]) -> List[str]:
        """
        Add multiple documents in bulk.

        Args:
            documents: List of dicts with keys: text, type, metadata, id (optional)

        Returns:
            List of document IDs
        """
        ids = []
        texts = []
        embeddings_list = []
        metadatas = []

        for doc in documents:
            text = doc["text"]
            doc_type = doc["type"]
            metadata = doc.get("metadata", {})
            doc_id = doc.get("id") or f"{doc_type}_{len(ids)}"

            ids.append(doc_id)
            texts.append(text)
            metadatas.append({"type": doc_type, **metadata})

        # Generate embeddings in batch
        embeddings_list = self.embeddings.embed_documents(texts)

        # Add to collection
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings_list,
            metadatas=metadatas,
        )

        return ids


# ============================================================================
# Convenience Functions
# ============================================================================


_rag_retriever: Optional[RAGRetriever] = None


def get_rag_retriever(
    persist_dir: str = "./data/vector_store",
    collection_name: str = "data_dictionary",
) -> RAGRetriever:
    """Get or create RAG retriever singleton."""
    global _rag_retriever
    if _rag_retriever is None:
        _rag_retriever = RAGRetriever(
            persist_dir=persist_dir, collection_name=collection_name
        )
    return _rag_retriever
