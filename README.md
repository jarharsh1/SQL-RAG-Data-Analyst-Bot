# SQL + RAG Data Analyst Bot

A production-grade AI-powered data analyst that combines Retrieval-Augmented Generation (RAG) with Text-to-SQL to answer business questions safely, accurately, and transparently.

## Features

- **Natural Language to SQL**: Convert business questions into accurate SQL queries
- **RAG-Based Context**: Retrieve metric definitions, data dictionaries, and business logic
- **Multi-Layer Safety**: Comprehensive validation, allowlists, and guardrails
- **Full Transparency**: Every query shows SQL, sources, and assumptions
- **Audit Trail**: Complete logging for compliance and debugging
- **Agentic Actions**: Optional exports, charts, and integrations

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL, MySQL, or Snowflake database (read-only access)
- OpenAI or Anthropic API key

### Installation

```bash
# Clone repository
git clone <repo-url>
cd SQL-RAG-Data-Analyst-Bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### Configuration

Edit `.env` file:

```bash
# LLM API Key (choose one)
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

# Database (read-only credentials)
DATABASE_URL=postgresql://readonly_user:password@localhost:5432/analytics
DATABASE_TYPE=postgresql
DATABASE_QUERY_TIMEOUT=30

# Safety settings
MAX_RESULT_ROWS=10000
ALLOWED_TABLES=orders,customers,products,order_line_items
BLOCKED_COLUMNS=ssn,credit_card_number,password
```

### Initialize Knowledge Base

```bash
# Populate vector store with your data dictionary
python scripts/init_knowledge_base.py \
  --metrics data/examples/metric_definitions.md \
  --dictionary data/examples/data_dictionary.yaml \
  --examples data/examples/golden_queries.sql
```

### Run Application

```bash
# Start FastAPI server
uvicorn src.main:app --reload --port 8000

# Or use the CLI
python src/cli.py "What was revenue by region last quarter?"
```

### API Usage

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What was revenue by region last quarter?",
    "user_id": "user@example.com"
  }'
```

## Project Structure

```
SQL-RAG-Data-Analyst-Bot/
├── ARCHITECTURE.md              # System design and architecture
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── pyproject.toml               # Python project config
│
├── src/
│   ├── main.py                  # FastAPI application entry point
│   ├── cli.py                   # Command-line interface
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py             # LangGraph state machine
│   │   ├── nodes.py             # State node implementations
│   │   └── state.py             # Agent state schemas
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── rag.py               # RAG retrieval system
│   │   ├── sql_generator.py    # Text-to-SQL generator
│   │   ├── sql_validator.py    # SQL safety validation
│   │   ├── sql_executor.py     # Database query executor
│   │   ├── question_parser.py  # Question understanding
│   │   └── result_interpreter.py # Result summarization
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py           # Pydantic models
│   │   └── config.py            # Configuration classes
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── audit_logger.py      # Audit trail logging
│   │   ├── llm_client.py        # LLM API client
│   │   └── db_client.py         # Database connection
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── export_csv.py        # CSV export tool
│   │   └── base.py              # Base tool interface
│   │
│   └── prompts/
│       ├── __init__.py
│       ├── sql_generation.py    # SQL generation prompts
│       ├── interpretation.py    # Result interpretation prompts
│       └── templates.py         # Prompt templates
│
├── tests/
│   ├── unit/
│   │   ├── test_sql_validator.py
│   │   ├── test_question_parser.py
│   │   └── test_rag.py
│   │
│   └── integration/
│       ├── test_agent_workflow.py
│       └── test_api.py
│
├── data/
│   ├── vector_store/            # ChromaDB persistence
│   ├── audit_logs/              # Query audit logs
│   └── examples/
│       ├── metric_definitions.md
│       ├── data_dictionary.yaml
│       └── golden_queries.sql
│
├── config/
│   ├── allowed_tables.yaml      # Table allowlist
│   └── sensitive_columns.yaml   # PII/sensitive columns
│
├── scripts/
│   ├── init_knowledge_base.py   # Setup vector store
│   └── test_connection.py       # Test database access
│
└── docs/
    ├── API.md                   # API documentation
    ├── DEPLOYMENT.md            # Deployment guide
    ├── SECURITY.md              # Security checklist
    └── EXAMPLES.md              # Example queries
```

## Core Components

### 1. Agent Orchestration (`src/agent/`)

LangGraph-based state machine that coordinates the entire workflow:

```
INTERPRET → RETRIEVE → PLAN → GENERATE_SQL → VALIDATE → EXECUTE → SUMMARIZE → RESPOND
```

### 2. RAG System (`src/core/rag.py`)

Retrieves relevant context from vector store:
- Metric definitions
- Data dictionary (tables, columns, relationships)
- Business rules and exclusions
- Example "golden" queries

### 3. SQL Generator (`src/core/sql_generator.py`)

Generates SQL queries using:
- User question
- Retrieved metric definitions
- Schema context
- LLM (GPT-4 or Claude)

### 4. SQL Validator (`src/core/sql_validator.py`)

Multi-layer safety validation:
- ✓ Operation whitelist (SELECT only)
- ✓ Table allowlist
- ✓ Column permissions
- ✓ Sensitive data masking
- ✓ Row limits and timeouts
- ✓ SQL injection prevention

### 5. Database Executor (`src/core/sql_executor.py`)

Safe query execution:
- Read-only connection
- Query timeout enforcement
- Result row limits
- Error handling

### 6. Audit Logger (`src/utils/audit_logger.py`)

Persistent audit trail:
- Every query logged
- User identity captured
- SQL and results metadata
- Timestamp and status

## Security & Safety

### Multi-Layer Defense

1. **SQL Validation**
   - Only SELECT statements allowed
   - Table and column allowlists
   - Sensitive column masking (PII)
   - Row limit enforcement (default: 10,000)
   - Query timeout (default: 30s)

2. **Database Safety**
   - Read-only database credentials
   - Connection pooling
   - Transaction rollback
   - No system table access

3. **Audit Trail**
   - All queries logged to `data/audit_logs/`
   - Includes user, SQL, timestamp, results metadata
   - Immutable append-only logs

4. **Data Protection**
   - Automatic PII detection
   - Configurable sensitive column blocklist
   - No credentials in logs

### Configuration Files

**Table Allowlist** (`config/allowed_tables.yaml`):
```yaml
allowed_tables:
  - orders
  - customers
  - products
  - order_line_items
  - sales_reps
```

**Sensitive Columns** (`config/sensitive_columns.yaml`):
```yaml
blocked_columns:
  - ssn
  - social_security_number
  - credit_card
  - credit_card_number
  - password
  - api_key
  - secret
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_sql_validator.py

# Run integration tests
pytest tests/integration/
```

## Example Usage

### CLI

```bash
# Ask a question
python src/cli.py "What was our top selling product last month?"

# With transparency
python src/cli.py "Show me revenue by region" --verbose

# Export results
python src/cli.py "Customer count by segment" --export results.csv
```

### Python API

```python
from src.agent.graph import create_analyst_graph
from src.models.schemas import QueryRequest

# Create agent
agent = create_analyst_graph()

# Ask question
request = QueryRequest(
    question="What was revenue by region last quarter?",
    user_id="analyst@company.com"
)

# Run agent
result = agent.invoke({"request": request})

print(result["response"].answer)
print(result["response"].transparency.sql_executed)
```

### REST API

```bash
# Query endpoint
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What was revenue by region last quarter?",
    "user_id": "user@example.com",
    "show_sql": true
  }'

# Health check
curl http://localhost:8000/health
```

## Deployment

### Docker

```bash
# Build image
docker build -t sql-rag-analyst .

# Run container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e DATABASE_URL=postgresql://... \
  -v $(pwd)/data:/app/data \
  sql-rag-analyst
```

### Production Checklist

- [ ] Configure read-only database user
- [ ] Set up table and column allowlists
- [ ] Populate knowledge base (metrics, dictionary)
- [ ] Configure authentication (JWT/OAuth)
- [ ] Set up monitoring and alerts
- [ ] Test SQL injection scenarios
- [ ] Review audit log retention
- [ ] Load test API endpoints
- [ ] Set up log aggregation
- [ ] Document runbooks

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed guide.

## Monitoring

### Metrics to Track

- Query latency (p50, p95, p99)
- SQL validation failures
- Database query timeouts
- LLM token usage and cost
- Error rates
- User activity

### Logs

- Application logs: `logs/app.log`
- Audit logs: `data/audit_logs/query_audit_YYYYMMDD.jsonl`

### Alerts

Set up alerts for:
- High validation failure rate
- Database connection errors
- LLM API failures
- Unusual query patterns

## Contributing

1. Follow existing code structure
2. Add unit tests for new features
3. Update documentation
4. Run `black` and `ruff` before committing
5. Ensure all tests pass

## License

MIT License - See LICENSE file

## Support

- Documentation: `docs/`
- Issues: GitHub Issues
- Security: See SECURITY.md

## Roadmap

- [ ] Support for more LLM providers (Azure, Vertex AI)
- [ ] Advanced chart generation
- [ ] Natural language result explanations with citations
- [ ] Multi-turn conversations with context
- [ ] Integration with BI tools (Tableau, Looker)
- [ ] Real-time query monitoring dashboard
- [ ] A/B testing for prompt optimization
- [ ] Query caching and optimization suggestions

---

**Built for production use. Safe, transparent, and auditable.**
