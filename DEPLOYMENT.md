# Deployment Guide - SQL + RAG Data Analyst Bot

Complete guide to deploying and running the full-stack application.

---

## Quick Start with Docker (Recommended)

The easiest way to get started is using Docker Compose, which sets up the entire stack:

```bash
# 1. Clone repository
git clone <repo-url>
cd SQL-RAG-Data-Analyst-Bot

# 2. Set up environment
cp .env.example .env
nano .env  # Add your OpenAI or Anthropic API key

# 3. Start all services
docker-compose up -d

# 4. Initialize knowledge base
docker-compose exec backend python scripts/init_knowledge_base.py

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

The stack includes:
- **Frontend**: React web app on port 3000
- **Backend**: FastAPI server on port 8000
- **Database**: PostgreSQL with sample data on port 5432

---

## Manual Setup (Development)

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (or MySQL/Snowflake)
- OpenAI or Anthropic API key

### Backend Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
nano .env  # Add your configuration

# 4. Set up database (example with PostgreSQL)
createdb analytics_db
psql analytics_db < scripts/init_db.sql

# 5. Initialize knowledge base
python scripts/init_knowledge_base.py

# 6. Start backend server
uvicorn src.main:app --reload --port 8000
```

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Configure environment
echo "VITE_API_URL=http://localhost:8000" > .env

# 4. Start development server
npm run dev
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## CLI Usage

The CLI tool provides a command-line interface for querying:

### Single Query Mode

```bash
python src/cli.py "What was revenue by region last quarter?"
```

### Interactive Mode

```bash
python src/cli.py --interactive
```

Then type your questions:

```
❯ What was revenue by region last quarter?
[Analyzes and displays results...]

❯ Show me top 10 products by sales
[Analyzes and displays results...]

❯ exit
```

### Advanced Options

```bash
# Specify user ID for audit logging
python src/cli.py "question here" --user-id analyst@company.com

# Get help
python src/cli.py --help
```

---

## Configuration

### Environment Variables (.env)

```bash
# LLM API Keys (required)
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# LLM Configuration
LLM_PROVIDER=openai  # or anthropic
LLM_MODEL=gpt-4-turbo-preview  # or claude-3-opus-20240229

# Database (required)
DATABASE_URL=postgresql://user:password@localhost:5432/analytics_db
DATABASE_TYPE=postgresql

# Safety (customize for your data)
MAX_RESULT_ROWS=10000
ALLOWED_TABLES=orders,customers,products,order_line_items
BLOCKED_COLUMNS=ssn,credit_card,password

# Paths
CHROMA_PERSIST_DIR=./data/vector_store
AUDIT_LOG_PATH=./data/audit_logs

# Application
APP_ENV=development
LOG_LEVEL=INFO
API_PORT=8000
```

### Customizing for Your Data

1. **Update Data Dictionary** (`data/examples/data_dictionary.yaml`):
   ```yaml
   tables:
     - name: your_table
       description: Your table description
       columns:
         - name: your_column
           type: VARCHAR
           description: Column description
   ```

2. **Add Metric Definitions** (`data/examples/metric_definitions.md`):
   ```markdown
   ### Your Metric Name
   - **Formula**: `SUM(your_table.amount)`
   - **Source Table**: `your_table`
   - **Grain**: `transaction_id`
   ```

3. **Reinitialize Knowledge Base**:
   ```bash
   python scripts/init_knowledge_base.py
   ```

---

## Production Deployment

### Docker Production Build

```bash
# Build optimized images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f backend
```

### Security Checklist

- [ ] Use read-only database credentials
- [ ] Configure `ALLOWED_TABLES` allowlist
- [ ] Set `BLOCKED_COLUMNS` for sensitive data
- [ ] Enable HTTPS (use nginx/traefik reverse proxy)
- [ ] Set up authentication (JWT/OAuth integration)
- [ ] Configure CORS properly
- [ ] Review and test SQL injection scenarios
- [ ] Set up log aggregation (ELK, Splunk)
- [ ] Configure monitoring and alerts
- [ ] Test rate limiting
- [ ] Backup vector store and audit logs
- [ ] Review audit logs retention policy

### Database Setup

1. **Create Read-Only User**:
   ```sql
   CREATE USER readonly_analyst WITH PASSWORD 'secure_password';
   GRANT CONNECT ON DATABASE analytics_db TO readonly_analyst;
   GRANT USAGE ON SCHEMA public TO readonly_analyst;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_analyst;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_analyst;
   ```

2. **Set Query Timeout** (PostgreSQL):
   ```sql
   ALTER USER readonly_analyst SET statement_timeout = '30s';
   ```

### Monitoring

1. **Health Checks**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Metrics to Track**:
   - Query latency (p50, p95, p99)
   - SQL validation failures
   - Database query timeouts
   - LLM token usage and costs
   - Error rates
   - Audit log volume

3. **Logs**:
   - Application logs: stdout/stderr
   - Audit logs: `data/audit_logs/query_audit_YYYYMMDD.jsonl`

### Scaling Considerations

For high-traffic deployments:

1. **Horizontal Scaling**:
   - Use load balancer (nginx, HAProxy)
   - Scale backend containers: `docker-compose up --scale backend=3`
   - Use Redis for shared state

2. **Caching**:
   - Cache LLM responses (Redis)
   - Cache RAG retrievals
   - Database query caching

3. **Database**:
   - Use connection pooling (already configured)
   - Read replicas for queries
   - Database-level query timeouts

4. **Vector Store**:
   - For large knowledge bases, consider hosted Chroma or Pinecone
   - Implement incremental updates

---

## Troubleshooting

### Backend Issues

**Issue**: `ModuleNotFoundError: No module named 'src'`
```bash
# Solution: Set PYTHONPATH
export PYTHONPATH=/path/to/SQL-RAG-Data-Analyst-Bot
```

**Issue**: `ConnectionRefusedError: [Errno 61] Connection refused (database)`
```bash
# Solution: Check database is running
docker-compose ps database
# Restart if needed
docker-compose restart database
```

**Issue**: `OpenAI API key not found`
```bash
# Solution: Check .env file
cat .env | grep OPENAI_API_KEY
# Reload environment
source .env  # or restart containers
```

### Frontend Issues

**Issue**: `CORS error when calling API`
```bash
# Solution: Update VITE_API_URL in frontend/.env
echo "VITE_API_URL=http://localhost:8000" > frontend/.env
# Restart frontend
npm run dev
```

**Issue**: `Module not found` errors
```bash
# Solution: Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Knowledge Base Issues

**Issue**: `No relevant context retrieved`
```bash
# Solution: Reinitialize knowledge base
python scripts/init_knowledge_base.py
# Check vector store
ls -la data/vector_store/
```

**Issue**: `ChromaDB connection error`
```bash
# Solution: Ensure directory exists
mkdir -p data/vector_store
# Check permissions
chmod 755 data/vector_store
```

### SQL Validation Issues

**Issue**: `Access denied to tables`
```bash
# Solution: Update ALLOWED_TABLES in .env
ALLOWED_TABLES=your_table_1,your_table_2,your_table_3
# Restart backend
```

**Issue**: `Query timeout`
```bash
# Solution: Increase timeout in .env
DATABASE_QUERY_TIMEOUT=60
MAX_QUERY_TIMEOUT_SECONDS=60
# Restart backend
```

---

## Testing

### Run Unit Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_sql_validator.py

# Verbose output
pytest -v
```

### Manual Testing

1. **Test Backend API**:
   ```bash
   curl -X POST http://localhost:8000/api/query \
     -H "Content-Type: application/json" \
     -d '{
       "question": "What was revenue by region last quarter?",
       "user_id": "test@example.com"
     }'
   ```

2. **Test CLI**:
   ```bash
   python src/cli.py "Show me total revenue"
   ```

3. **Test Frontend**:
   - Open http://localhost:3000
   - Type a question and verify response
   - Check SQL display works
   - Test CSV export

---

## Backup and Restore

### Backup

```bash
# Backup database
docker-compose exec database pg_dump -U analyst_user analytics_db > backup.sql

# Backup vector store
tar -czf vector_store_backup.tar.gz data/vector_store/

# Backup audit logs
tar -czf audit_logs_backup.tar.gz data/audit_logs/
```

### Restore

```bash
# Restore database
docker-compose exec -T database psql -U analyst_user analytics_db < backup.sql

# Restore vector store
tar -xzf vector_store_backup.tar.gz

# Restore audit logs
tar -xzf audit_logs_backup.tar.gz
```

---

## API Documentation

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Or use the OpenAPI schema at http://localhost:8000/openapi.json

---

## Support

- **Documentation**: See README.md and ARCHITECTURE.md
- **Issues**: GitHub Issues
- **Security**: See SECURITY.md (create for production)

---

## Next Steps

1. Customize data dictionary for your database schema
2. Add your metric definitions
3. Configure authentication/authorization
4. Set up monitoring and alerting
5. Deploy to production environment
6. Train users on supported question types
7. Monitor usage and optimize prompts

Good luck! 🚀
