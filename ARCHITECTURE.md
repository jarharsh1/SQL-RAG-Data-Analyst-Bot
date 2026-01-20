# SQL + RAG Data Analyst Bot - System Architecture

## Overview

This is a production-grade AI-powered data analyst that combines Retrieval-Augmented Generation (RAG) with Text-to-SQL capabilities to answer business questions safely and transparently.

**Core Capabilities:**
- Natural language business questions → Accurate SQL queries
- RAG-based metric definitions and business logic retrieval
- Multi-layer safety validation and guardrails
- Full transparency with citations and SQL visibility
- Audit logging for compliance and debugging
- Optional agentic actions (exports, alerts, tickets)

---

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (API / CLI / Web UI)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                        │
│                     /api/query endpoint                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Agent Orchestrator                 │
│                      (State Machine Workflow)                   │
│                                                                 │
│  States: INTERPRET → RETRIEVE → PLAN → GENERATE →              │
│          VALIDATE → EXECUTE → SUMMARIZE → RESPOND               │
└─────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
    │Question│   │   RAG    │   │Text-to-  │   │   SQL    │
    │Parser  │   │Retrieval │   │   SQL    │   │Validator │
    └────────┘   └──────────┘   └──────────┘   └──────────┘
                      │              │              │
                      ▼              ▼              ▼
                 ┌─────────────────────────────────────┐
                 │        Vector Store (Chroma)       │
                 │  - Metric definitions              │
                 │  - Data dictionary                 │
                 │  - Business rules                  │
                 │  - Example queries                 │
                 └─────────────────────────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  SQL Executor   │
                          │ (Read-only DB)  │
                          └─────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  Result         │
                          │  Interpreter    │
                          └─────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  Audit Logger   │
                          │  (Persistent)   │
                          └─────────────────┘
```

---

## Agent Workflow (State Machine)

The system uses a **finite state machine** to ensure safe, transparent, and auditable processing:

### State Flow

```
START
  │
  ├─> 1. INTERPRET
  │     │ Parse user question
  │     │ Identify intent, metrics, dimensions, timeframes
  │     │ Determine if SQL execution is needed
  │     │
  │     ├─> Decision: Need clarification?
  │     │     YES → ASK_CLARIFICATION → (wait for user) → INTERPRET
  │     │     NO  → Continue
  │     │
  │     └─> Output: ParsedQuestion
  │
  ├─> 2. RETRIEVE (RAG)
  │     │ Query vector store for:
  │     │   - Metric definitions
  │     │   - Data dictionary
  │     │   - Business rules
  │     │   - Example queries
  │     │ Collect citations
  │     │
  │     └─> Output: RetrievedContext + Citations
  │
  ├─> 3. PLAN
  │     │ Determine query strategy
  │     │ Identify required tables and joins
  │     │ Check user permissions
  │     │ Apply business logic
  │     │
  │     └─> Output: QueryPlan
  │
  ├─> 4. GENERATE_SQL
  │     │ Generate SQL using:
  │     │   - User question
  │     │   - Retrieved definitions
  │     │   - Schema context
  │     │   - Query plan
  │     │
  │     └─> Output: GeneratedSQL
  │
  ├─> 5. VALIDATE
  │     │ Multi-layer validation:
  │     │   ✓ SQL parsing (syntax)
  │     │   ✓ Operation whitelist (SELECT only)
  │     │   ✓ Table allowlist
  │     │   ✓ Column permissions
  │     │   ✓ Row limit enforcement
  │     │   ✓ Sensitive data masking
  │     │
  │     ├─> Decision: SQL safe?
  │     │     NO  → REWRITE or ASK_CLARIFICATION
  │     │     YES → Continue
  │     │
  │     └─> Output: ValidatedSQL
  │
  ├─> 6. EXECUTE
  │     │ Execute SQL with:
  │     │   - Read-only connection
  │     │   - Query timeout
  │     │   - Result row limit
  │     │ Capture metadata (time, rows, errors)
  │     │
  │     ├─> Decision: Execution successful?
  │     │     NO  → ERROR_HANDLER → RESPOND
  │     │     YES → Continue
  │     │
  │     └─> Output: QueryResult + Metadata
  │
  ├─> 7. SUMMARIZE
  │     │ Interpret results:
  │     │   - Convert to business language
  │     │   - Identify trends/anomalies
  │     │   - Apply formatting
  │     │ NO hallucination beyond returned data
  │     │
  │     └─> Output: Summary
  │
  ├─> 8. RESPOND
  │     │ Build response with:
  │     │   - Summary
  │     │   - Transparency section:
  │     │       * SQL used
  │     │       * Definitions applied
  │     │       * Tables queried
  │     │       * Assumptions
  │     │   - Suggested actions (optional)
  │     │
  │     └─> Output: FinalResponse
  │
  └─> 9. AUDIT
        │ Log to persistent storage:
        │   - User question
        │   - SQL executed
        │   - Data sources
        │   - Result metadata
        │   - Timestamp, user_id
        │
        └─> END
```

### State Transitions

| From State      | To State(s)          | Condition                          |
|-----------------|----------------------|------------------------------------|
| INTERPRET       | RETRIEVE             | Question understood                |
| INTERPRET       | ASK_CLARIFICATION    | Ambiguous or incomplete            |
| RETRIEVE        | PLAN                 | Context retrieved                  |
| PLAN            | GENERATE_SQL         | SQL needed                         |
| PLAN            | SUMMARIZE            | Only RAG response needed           |
| GENERATE_SQL    | VALIDATE             | SQL generated                      |
| VALIDATE        | EXECUTE              | SQL safe                           |
| VALIDATE        | GENERATE_SQL         | SQL unsafe, attempt rewrite        |
| VALIDATE        | ASK_CLARIFICATION    | Cannot safely generate SQL         |
| EXECUTE         | SUMMARIZE            | Execution successful               |
| EXECUTE         | ERROR_HANDLER        | Execution failed                   |
| SUMMARIZE       | RESPOND              | Always                             |
| RESPOND         | AUDIT                | Always                             |
| AUDIT           | END                  | Always                             |
| ERROR_HANDLER   | RESPOND              | Always                             |
| ASK_CLARIFICATION| INTERPRET           | User responds                      |

---

## Data Flow

### 1. Input Processing
```
User Question (Natural Language)
    │
    ├─> Question Parser
    │     - Extract entities (metrics, dimensions, dates)
    │     - Identify intent (trend, comparison, definition)
    │     - Normalize language
    │
    └─> ParsedQuestion Schema
          {
            "question": "original question",
            "intent": "comparison",
            "metrics": ["revenue", "profit_margin"],
            "dimensions": ["region", "product_category"],
            "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "filters": ["region = 'North America'"]
          }
```

### 2. Knowledge Retrieval (RAG)
```
ParsedQuestion
    │
    ├─> Vector Store Query
    │     - Semantic search for metric definitions
    │     - Retrieve data dictionary entries
    │     - Find relevant business rules
    │     - Pull example queries
    │
    └─> RetrievedContext Schema
          {
            "metric_definitions": [
              {
                "name": "revenue",
                "formula": "SUM(order_line_items.price * quantity)",
                "source_table": "order_line_items",
                "grain": "order_id",
                "citation": "metric_definitions.md:42"
              }
            ],
            "table_metadata": [...],
            "business_rules": [...],
            "example_queries": [...]
          }
```

### 3. SQL Generation
```
ParsedQuestion + RetrievedContext + Schema
    │
    ├─> LLM (Text-to-SQL)
    │     Prompt Template:
    │     - System: "You are a SQL expert..."
    │     - Context: Metric definitions, schema, rules
    │     - Task: Generate SELECT query
    │     - Constraints: Read-only, use definitions
    │
    └─> GeneratedSQL
          {
            "sql": "SELECT ... FROM ... WHERE ...",
            "tables_used": ["orders", "order_line_items"],
            "definitions_applied": ["revenue"],
            "assumptions": ["Excluding cancelled orders"]
          }
```

### 4. Validation & Safety
```
GeneratedSQL
    │
    ├─> SQL Validator (Multi-layer)
    │     1. Parse SQL (sqlglot)
    │     2. Check operation type (SELECT only)
    │     3. Validate tables (allowlist)
    │     4. Validate columns (permissions + sensitive data)
    │     5. Enforce limits (rows, timeout)
    │     6. Inject safety filters
    │
    ├─> Decision: Safe?
    │     NO  → ValidationError → Rewrite or Clarify
    │     YES → ValidatedSQL
    │
    └─> ValidatedSQL
          {
            "sql": "SELECT ... LIMIT 10000",
            "safety_checks": {
              "operation_type": "SELECT",
              "tables_validated": true,
              "columns_validated": true,
              "row_limit": 10000,
              "timeout_seconds": 30
            }
          }
```

### 5. Execution
```
ValidatedSQL
    │
    ├─> Database Executor (Read-only)
    │     - Use read-only credentials
    │     - Apply query timeout
    │     - Capture execution metadata
    │
    └─> QueryResult
          {
            "data": [...rows...],
            "columns": ["region", "revenue"],
            "row_count": 42,
            "execution_time_ms": 1234,
            "truncated": false
          }
```

### 6. Interpretation
```
QueryResult + ParsedQuestion + Definitions
    │
    ├─> Result Interpreter (LLM)
    │     - Summarize findings
    │     - Identify trends
    │     - Apply business context
    │     - Format for presentation
    │
    └─> Summary
          {
            "summary": "Revenue in North America was $5.2M...",
            "insights": ["Revenue increased 23% YoY", "Top region: Northeast"],
            "data_formatted": {...}
          }
```

### 7. Response Construction
```
Summary + SQL + Definitions + Metadata
    │
    └─> FinalResponse
          {
            "answer": "Revenue in North America was $5.2M...",
            "transparency": {
              "sql_executed": "SELECT ...",
              "definitions_used": [...],
              "tables_accessed": ["orders", "order_line_items"],
              "assumptions": [...],
              "citations": [...]
            },
            "data": {...},
            "metadata": {
              "execution_time_ms": 1234,
              "rows_returned": 42
            },
            "suggested_actions": [
              {"type": "export_csv", "label": "Download as CSV"},
              {"type": "chart", "label": "Visualize trend"}
            ]
          }
```

---

## Technology Stack

### Core Framework
- **FastAPI**: REST API framework
- **LangGraph**: Agent orchestration and state management
- **LangChain**: LLM integration and prompt management

### LLM & Embeddings
- **OpenAI GPT-4** or **Claude 3.5 Sonnet**: Text-to-SQL, interpretation
- **OpenAI text-embedding-3-small**: Vector embeddings for RAG

### Vector Store
- **ChromaDB**: Local/persistent vector database for knowledge base

### Database
- **SQLAlchemy**: Database abstraction layer
- **PostgreSQL/MySQL/Snowflake**: Supported databases (read-only)
- **sqlglot**: SQL parsing and validation

### Validation & Safety
- **Pydantic v2**: Data validation and serialization
- **sqlparse**: SQL syntax parsing
- **sqlglot**: SQL dialect translation and AST analysis

### Logging & Monitoring
- **Structlog**: Structured logging
- **Custom audit logger**: Persistent audit trail

### Development & Testing
- **Pytest**: Unit and integration tests
- **Black**: Code formatting
- **Ruff**: Linting
- **Mypy**: Type checking

---

## Security & Safety

### Multi-Layer Defense

1. **Authentication & Authorization** (Not implemented - integrate with your system)
   - User authentication via JWT/OAuth
   - Role-based access control (RBAC)
   - Row-level security policies

2. **SQL Safety Validation**
   - ✓ Operation whitelist (SELECT only)
   - ✓ Table allowlist enforcement
   - ✓ Column permission checks
   - ✓ Sensitive column masking (PII, credentials)
   - ✓ Row limit enforcement (max 10,000 rows)
   - ✓ Query timeout (max 30 seconds)
   - ✓ SQL injection prevention (parameterized queries)
   - ✓ Subquery depth limits
   - ✓ No system table access

3. **Database Connection Safety**
   - Read-only database user
   - Connection pooling with limits
   - Query timeout enforcement
   - Transaction rollback on errors

4. **Data Protection**
   - Automatic PII detection and masking
   - Sensitive column blocklist
   - Result row truncation
   - No credential storage in logs

5. **Rate Limiting** (To be implemented)
   - Per-user request limits
   - Concurrent query limits
   - Token budget management

6. **Audit Trail**
   - Every query logged
   - User identity captured
   - Timestamp and metadata
   - Immutable audit log

---

## Deployment Considerations

### Environment Variables
```
# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database (Read-only)
DATABASE_URL=postgresql://readonly_user:password@host:5432/db
DATABASE_TYPE=postgresql
DATABASE_QUERY_TIMEOUT=30

# Vector Store
CHROMA_PERSIST_DIR=/data/chroma
CHROMA_COLLECTION_NAME=data_dictionary

# Safety
MAX_RESULT_ROWS=10000
ALLOWED_TABLES=orders,customers,products,order_line_items
BLOCKED_COLUMNS=ssn,credit_card,password,api_key

# Audit
AUDIT_LOG_PATH=/data/audit/query_audit.jsonl

# App
LOG_LEVEL=INFO
```

### Docker Deployment
- Use multi-stage builds
- Run as non-root user
- Mount audit logs and vector store as volumes
- Use secrets management for credentials

### Monitoring
- Log all queries and latencies
- Alert on validation failures
- Track token usage
- Monitor database connection pool

---

## Assumptions & Design Decisions

1. **RAG Knowledge Base**: Assumes you will populate the vector store with:
   - Metric definitions (Markdown or JSON)
   - Data dictionary (table/column metadata)
   - Business rules and exclusions
   - Example "golden" queries

2. **Database Access**: System assumes read-only database user with:
   - SELECT-only permissions
   - Access limited to approved schemas/tables
   - Query timeout enforced at DB level

3. **User Authentication**: Framework is auth-agnostic. Integrate with your existing:
   - SSO/OAuth provider
   - RBAC system
   - Row-level security policies

4. **LLM Provider**: Default is OpenAI, but supports:
   - Anthropic Claude
   - Azure OpenAI
   - Local models via Ollama (with appropriate prompts)

5. **SQL Dialect**: Configurable via sqlglot for:
   - PostgreSQL
   - MySQL
   - Snowflake
   - BigQuery
   - Others (via dialect param)

6. **Agentic Actions**: Tool framework provided, but specific integrations (Jira, Slack, etc.) must be implemented based on your environment

7. **Scalability**: Current design is for single-instance deployment. For scale:
   - Use Redis for state persistence
   - Implement job queue (Celery)
   - Cache LLM responses
   - Load balance across instances

---

## Next Steps for Production

1. **Knowledge Base Setup**
   - Ingest metric definitions
   - Build data dictionary
   - Create embeddings
   - Test retrieval quality

2. **Database Configuration**
   - Create read-only user
   - Configure allowlists
   - Test permissions
   - Set up connection pooling

3. **Testing**
   - Unit tests for validators
   - Integration tests for workflow
   - Load testing for API
   - Penetration testing for SQL injection

4. **Monitoring & Alerts**
   - Set up log aggregation
   - Configure error alerts
   - Track usage metrics
   - Monitor costs (LLM tokens)

5. **User Training**
   - Document supported question types
   - Provide example questions
   - Explain transparency features
   - Train on edge cases

6. **Compliance**
   - Review with security team
   - Validate audit logging
   - Ensure GDPR/CCPA compliance
   - Document data flows

---

## Example End-to-End Flow

**User Question**: "What was our revenue by region last quarter?"

**Flow**:
1. **INTERPRET**: Parse → metrics=[revenue], dimensions=[region], time_range=Q4-2024
2. **RETRIEVE**: Find "revenue" definition → "SUM(order_line_items.price * quantity)"
3. **PLAN**: Need tables: orders, order_line_items, customers (for region)
4. **GENERATE_SQL**:
   ```sql
   SELECT
     c.region,
     SUM(oli.price * oli.quantity) as revenue
   FROM orders o
   JOIN order_line_items oli ON o.order_id = oli.order_id
   JOIN customers c ON o.customer_id = c.customer_id
   WHERE o.order_date >= '2024-10-01'
     AND o.order_date < '2025-01-01'
     AND o.status != 'cancelled'
   GROUP BY c.region
   ORDER BY revenue DESC
   LIMIT 10000
   ```
5. **VALIDATE**: ✓ SELECT only, ✓ tables allowed, ✓ columns safe, ✓ limit applied
6. **EXECUTE**: Run query → 4 rows returned in 234ms
7. **SUMMARIZE**: "Revenue last quarter: North America $5.2M, Europe $3.1M, Asia $2.8M, South America $1.1M. Total: $12.2M"
8. **RESPOND**: Return summary + SQL + transparency
9. **AUDIT**: Log query, SQL, user, timestamp

**Response to User**:
```json
{
  "answer": "Last quarter (Q4 2024), total revenue was $12.2M across four regions. North America led with $5.2M (43%), followed by Europe at $3.1M (25%), Asia at $2.8M (23%), and South America at $1.1M (9%).",

  "transparency": {
    "sql_executed": "SELECT c.region, SUM(oli.price * oli.quantity) as revenue FROM ...",
    "definitions_used": [
      {
        "metric": "revenue",
        "formula": "SUM(order_line_items.price * quantity)",
        "source": "metric_definitions.md:42"
      }
    ],
    "tables_accessed": ["orders", "order_line_items", "customers"],
    "assumptions": [
      "Excluded cancelled orders per business rules",
      "Last quarter = Q4 2024 (Oct 1 - Dec 31)"
    ]
  },

  "data": {
    "columns": ["region", "revenue"],
    "rows": [
      ["North America", 5200000],
      ["Europe", 3100000],
      ["Asia", 2800000],
      ["South America", 1100000]
    ]
  },

  "metadata": {
    "execution_time_ms": 234,
    "rows_returned": 4,
    "timestamp": "2024-01-20T10:30:00Z"
  }
}
```

