-- Golden Query Examples
-- These are well-formed SQL queries that serve as examples for the LLM

-- Example 1: Revenue by Region
-- Question: "What is revenue by region?"
SELECT
  c.region,
  SUM(oli.price * oli.quantity) as revenue,
  COUNT(DISTINCT o.order_id) as order_count,
  COUNT(DISTINCT c.customer_id) as customer_count
FROM orders o
JOIN order_line_items oli ON o.order_id = oli.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status != 'cancelled'
GROUP BY c.region
ORDER BY revenue DESC
LIMIT 10000;

-- Example 2: Top Products by Revenue
-- Question: "What are the top 10 products by revenue?"
SELECT
  p.product_name,
  p.category,
  SUM(oli.price * oli.quantity) as product_revenue,
  SUM(oli.quantity) as units_sold,
  AVG(oli.price) as avg_selling_price
FROM order_line_items oli
JOIN products p ON oli.product_id = p.product_id
JOIN orders o ON oli.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY product_revenue DESC
LIMIT 10;

-- Example 3: Monthly Revenue Trend
-- Question: "Show monthly revenue for 2024"
SELECT
  DATE_TRUNC('month', o.order_date) as month,
  SUM(oli.price * oli.quantity) as revenue,
  COUNT(DISTINCT o.order_id) as orders,
  SUM(oli.price * oli.quantity) / COUNT(DISTINCT o.order_id) as avg_order_value
FROM orders o
JOIN order_line_items oli ON o.order_id = oli.order_id
WHERE o.status = 'completed'
  AND o.order_date >= '2024-01-01'
  AND o.order_date < '2025-01-01'
GROUP BY DATE_TRUNC('month', o.order_date)
ORDER BY month
LIMIT 10000;

-- Example 4: Customer Lifetime Value
-- Question: "What is the average customer lifetime value?"
SELECT
  AVG(customer_total) as avg_lifetime_value,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY customer_total) as median_lifetime_value,
  MAX(customer_total) as max_lifetime_value
FROM (
  SELECT
    c.customer_id,
    SUM(oli.price * oli.quantity) as customer_total
  FROM customers c
  JOIN orders o ON c.customer_id = o.customer_id
  JOIN order_line_items oli ON o.order_id = oli.order_id
  WHERE o.status = 'completed'
    AND c.status = 'active'
  GROUP BY c.customer_id
) customer_totals
LIMIT 10000;

-- Example 5: Year-over-Year Comparison
-- Question: "Compare revenue this year vs last year by region"
SELECT
  c.region,
  SUM(CASE WHEN EXTRACT(YEAR FROM o.order_date) = 2024 THEN oli.price * oli.quantity ELSE 0 END) as revenue_2024,
  SUM(CASE WHEN EXTRACT(YEAR FROM o.order_date) = 2023 THEN oli.price * oli.quantity ELSE 0 END) as revenue_2023,
  (SUM(CASE WHEN EXTRACT(YEAR FROM o.order_date) = 2024 THEN oli.price * oli.quantity ELSE 0 END) -
   SUM(CASE WHEN EXTRACT(YEAR FROM o.order_date) = 2023 THEN oli.price * oli.quantity ELSE 0 END)) /
   NULLIF(SUM(CASE WHEN EXTRACT(YEAR FROM o.order_date) = 2023 THEN oli.price * oli.quantity ELSE 0 END), 0) * 100 as yoy_growth_percent
FROM orders o
JOIN order_line_items oli ON o.order_id = oli.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
  AND EXTRACT(YEAR FROM o.order_date) IN (2023, 2024)
GROUP BY c.region
ORDER BY revenue_2024 DESC
LIMIT 10000;

-- Example 6: New vs Returning Customers
-- Question: "How many new vs returning customers placed orders last month?"
SELECT
  CASE
    WHEN order_count = 1 THEN 'New Customer'
    ELSE 'Returning Customer'
  END as customer_type,
  COUNT(*) as customer_count,
  SUM(total_revenue) as revenue,
  AVG(total_revenue) as avg_revenue_per_customer
FROM (
  SELECT
    c.customer_id,
    COUNT(DISTINCT o.order_id) as order_count,
    SUM(oli.price * oli.quantity) as total_revenue
  FROM customers c
  JOIN orders o ON c.customer_id = o.customer_id
  JOIN order_line_items oli ON o.order_id = oli.order_id
  WHERE o.order_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
    AND o.order_date < DATE_TRUNC('month', CURRENT_DATE)
    AND o.status = 'completed'
  GROUP BY c.customer_id
) customer_orders
GROUP BY customer_type
LIMIT 10000;

-- Example 7: Product Category Performance
-- Question: "Show product category performance with margin analysis"
SELECT
  p.category,
  SUM(oli.quantity) as units_sold,
  SUM(oli.price * oli.quantity) as revenue,
  SUM(p.cost * oli.quantity) as cost,
  SUM(oli.price * oli.quantity) - SUM(p.cost * oli.quantity) as gross_profit,
  (SUM(oli.price * oli.quantity) - SUM(p.cost * oli.quantity)) /
    NULLIF(SUM(oli.price * oli.quantity), 0) * 100 as profit_margin_percent
FROM products p
JOIN order_line_items oli ON p.product_id = oli.product_id
JOIN orders o ON oli.order_id = o.order_id
WHERE o.status = 'completed'
  AND p.status = 'active'
GROUP BY p.category
ORDER BY revenue DESC
LIMIT 10000;
