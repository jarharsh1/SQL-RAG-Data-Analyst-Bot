# CSV Mode - No Database Required!

Run the SQL + RAG Data Analyst without needing any database setup. Perfect for demos, testing, and quick prototyping.

---

## What is CSV Mode?

CSV Mode allows you to query CSV files using SQL - no PostgreSQL, MySQL, or Snowflake required! The system:

1. **Generates realistic sample data** as CSV files
2. **Queries CSVs with SQL** using DuckDB (in-memory analytics database)
3. **Works with the exact same UI and API** as the full version

This is perfect for:
- 🚀 **Quick demos** - Get started in under 2 minutes
- 🧪 **Testing** - Try the system without database setup
- 📚 **Learning** - Understand how RAG + Text-to-SQL works
- 🎓 **Tutorials** - Teach AI data analysis concepts

---

## Quick Start (2 Minutes)

### Step 1: Generate Sample CSV Data

```bash
# Generate realistic sample data (customers, products, orders)
python scripts/generate_sample_data.py

# This creates data/csv/ with:
# - customers.csv (100 customers)
# - products.csv (50 products)
# - orders.csv (500 orders)
# - order_line_items.csv (line items)
# - sales_reps.csv (sales representatives)
```

### Step 2: Initialize Knowledge Base

```bash
# Load CSV metadata into vector store
python scripts/init_csv_metadata.py

# This creates table metadata and metric definitions
# that help the LLM understand your data
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set:
nano .env
```

Make sure these are set:
```bash
OPENAI_API_KEY=sk-your-api-key-here
DATABASE_TYPE=csv  # <-- This enables CSV mode!
CSV_DATA_DIR=./data/csv
```

### Step 4: Run!

```bash
# Option 1: Web UI
uvicorn src.main:app --reload
# Then open http://localhost:3000

# Option 2: CLI
python src/cli.py "What was revenue by region last quarter?"

# Option 3: Interactive CLI
python src/cli.py --interactive
```

---

## Example Questions

Try these questions with your CSV data:

### Revenue Analysis
- "What was total revenue last quarter?"
- "Show me revenue by region"
- "What's the revenue trend by month?"

### Customer Analysis
- "How many customers do we have by region?"
- "Who are the top 10 customers by lifetime value?"
- "What's the average customer lifetime value?"

### Product Analysis
- "What are the top selling products?"
- "Show me product sales by category"
- "Which products have the highest margin?"

### Order Analysis
- "How many orders were placed last month?"
- "What's the average order value?"
- "Show me order status distribution"

---

## How It Works

### 1. DuckDB - In-Memory SQL Database

Instead of PostgreSQL or MySQL, CSV mode uses [DuckDB](https://duckdb.org/):

- **In-memory** - No database server required
- **Fast** - Columnar storage, vectorized execution
- **SQL compatible** - Standard SQL syntax
- **CSV native** - Reads CSV files directly

### 2. Automatic Table Registration

When the system starts, it automatically:

```python
# Finds all CSV files in data/csv/
customers.csv → customers table
products.csv → products table
orders.csv → orders table
```

### 3. SQL Query Execution

Your natural language question:
```
"What was revenue by region last quarter?"
```

Gets converted to SQL:
```sql
SELECT
  region,
  SUM(total_amount) as revenue
FROM orders
WHERE order_date >= '2024-10-01'
  AND order_date < '2025-01-01'
  AND status = 'completed'
GROUP BY region
ORDER BY revenue DESC
```

DuckDB executes this SQL directly on the CSV files and returns results!

---

## Customizing Your Data

### Generating More Data

```bash
# Generate 1000 customers, 100 products, 5000 orders
python scripts/generate_sample_data.py \
  --num-customers 1000 \
  --num-products 100 \
  --num-orders 5000
```

### Using Your Own CSV Files

1. **Place CSVs in `data/csv/`**:
   ```
   data/csv/
   ├── your_table1.csv
   ├── your_table2.csv
   └── your_table3.csv
   ```

2. **Ensure CSVs have headers**:
   ```csv
   customer_id,name,email,region
   1,John Doe,john@example.com,North America
   2,Jane Smith,jane@example.com,Europe
   ```

3. **Initialize metadata**:
   ```bash
   python scripts/init_csv_metadata.py
   ```

4. **Update allowed tables** in `.env`:
   ```bash
   ALLOWED_TABLES=your_table1,your_table2,your_table3
   ```

### Adding Custom Metrics

Edit the metric definitions in `scripts/init_csv_metadata.py`:

```python
metrics = [
    {
        "name": "Your Custom Metric",
        "formula": "SUM(your_column)",
        "description": "Description of your metric",
        "source_table": "your_table",
        "filters": "WHERE condition",
    },
]
```

Then re-run:
```bash
python scripts/init_csv_metadata.py
```

---

## Sample Data Schema

The generated CSV data includes:

### Customers (100 rows)
- `customer_id` - Unique ID
- `email` - Email address
- `first_name`, `last_name` - Name
- `region` - North America, Europe, Asia, South America
- `country` - Specific country
- `status` - active, inactive
- `signup_date` - Registration date
- `total_orders` - Number of orders
- `lifetime_value` - Total spent

### Products (50 rows)
- `product_id` - Unique ID
- `product_name` - Product name
- `category` - Electronics, Furniture, Office Supplies
- `subcategory` - Specific subcategory
- `unit_price` - Selling price
- `cost` - Cost of goods
- `margin` - Profit margin percentage
- `status` - active, discontinued
- `stock_quantity` - Current stock

### Orders (500 rows)
- `order_id` - Unique ID
- `customer_id` - FK to customers
- `order_date` - Date placed
- `order_quarter` - Q1, Q2, Q3, Q4
- `order_year` - Year
- `status` - pending, completed, shipped, cancelled
- `subtotal` - Before tax
- `tax_amount` - Sales tax
- `shipping_amount` - Shipping cost
- `total_amount` - Final total
- `num_items` - Item count
- `region`, `country` - From customer

### Order Line Items (varies)
- `line_item_id` - Unique ID
- `order_id` - FK to orders
- `product_id` - FK to products
- `product_name` - Product name
- `quantity` - Units ordered
- `unit_price` - Price at time of order
- `discount_amount` - Discount applied
- `line_total` - Line item total

### Sales Reps (10 rows)
- `rep_id` - Unique ID
- `first_name`, `last_name` - Name
- `email` - Email address
- `region` - Assigned region
- `hire_date` - Date hired
- `tenure_days` - Days employed
- `status` - active, on_leave

---

## Limitations of CSV Mode

While CSV mode is great for demos and testing, be aware:

1. **Performance** - Large CSV files (>1GB) may be slow
2. **No Joins Optimization** - Not as efficient as a real database for complex joins
3. **No Indexes** - Cannot create indexes on CSV data
4. **Single-User** - Not designed for concurrent access
5. **No Persistence** - Changes aren't saved back to CSV

For production use with large datasets, use a real database (PostgreSQL, MySQL, Snowflake).

---

## Switching Between CSV and Database Mode

### To CSV Mode:
```bash
# In .env
DATABASE_TYPE=csv
CSV_DATA_DIR=./data/csv
```

### To Database Mode:
```bash
# In .env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@localhost:5432/db
```

The same application code works for both!

---

## Troubleshooting

### "No CSV files found"

```bash
# Run the generator first
python scripts/generate_sample_data.py
```

### "Module 'duckdb' not found"

```bash
# Install dependencies
pip install -r requirements.txt
```

### "No tables registered"

Check that:
1. CSVs exist in `data/csv/`
2. CSVs have valid headers
3. `CSV_DATA_DIR` in `.env` points to correct directory

### "Table not found" error

Update allowed tables in `.env`:
```bash
ALLOWED_TABLES=customers,products,orders,order_line_items
```

---

## Advanced: Querying CSVs Directly

You can also use DuckDB directly:

```python
import duckdb

# Connect to in-memory database
con = duckdb.connect(':memory:')

# Query CSV directly
result = con.execute("""
    SELECT *
    FROM read_csv_auto('data/csv/customers.csv')
    LIMIT 10
""").fetchall()

print(result)
```

Or use the CSV executor:

```python
from src.core.csv_executor import CSVExecutor

executor = CSVExecutor('./data/csv')

# List all tables
tables = executor.list_tables()
print(tables)

# Get table info
info = executor.get_table_info('customers')
print(info)
```

---

## Next Steps

1. **Try different questions** - See what insights you can find
2. **Generate more data** - Scale up to test performance
3. **Add your own CSVs** - Use real data from your business
4. **Switch to database** - When ready for production

Happy querying! 🚀
