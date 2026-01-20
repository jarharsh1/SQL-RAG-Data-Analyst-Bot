-- Initialize sample database for SQL + RAG Analyst
-- This creates example tables with sample data for testing

-- Create tables
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    region VARCHAR(50),
    country VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    unit_price DECIMAL(10, 2),
    cost DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    total_amount DECIMAL(12, 2),
    subtotal DECIMAL(12, 2),
    tax_amount DECIMAL(12, 2),
    shipping_amount DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_line_items (
    line_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sales_reps (
    rep_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    region VARCHAR(50),
    hire_date DATE
);

-- Insert sample data
INSERT INTO customers (email, first_name, last_name, region, country, status) VALUES
('john.doe@example.com', 'John', 'Doe', 'North America', 'USA', 'active'),
('jane.smith@example.com', 'Jane', 'Smith', 'Europe', 'UK', 'active'),
('bob.johnson@example.com', 'Bob', 'Johnson', 'North America', 'Canada', 'active'),
('alice.brown@example.com', 'Alice', 'Brown', 'Asia', 'Japan', 'active'),
('charlie.wilson@example.com', 'Charlie', 'Wilson', 'Europe', 'Germany', 'active'),
('diana.martinez@example.com', 'Diana', 'Martinez', 'South America', 'Brazil', 'active'),
('edward.taylor@example.com', 'Edward', 'Taylor', 'North America', 'USA', 'active'),
('fiona.anderson@example.com', 'Fiona', 'Anderson', 'Europe', 'France', 'active'),
('george.thomas@example.com', 'George', 'Thomas', 'Asia', 'India', 'active'),
('helen.jackson@example.com', 'Helen', 'Jackson', 'North America', 'USA', 'active')
ON CONFLICT (email) DO NOTHING;

INSERT INTO products (product_name, category, subcategory, unit_price, cost, status) VALUES
('Laptop Pro 15"', 'Electronics', 'Computers', 1299.99, 800.00, 'active'),
('Wireless Mouse', 'Electronics', 'Accessories', 29.99, 12.00, 'active'),
('Office Chair Premium', 'Furniture', 'Chairs', 449.99, 200.00, 'active'),
('Desk Lamp LED', 'Furniture', 'Lighting', 79.99, 30.00, 'active'),
('Notebook Set', 'Office Supplies', 'Paper', 19.99, 5.00, 'active'),
('USB-C Cable', 'Electronics', 'Accessories', 14.99, 3.00, 'active'),
('Monitor 27"', 'Electronics', 'Displays', 399.99, 250.00, 'active'),
('Keyboard Mechanical', 'Electronics', 'Accessories', 129.99, 60.00, 'active'),
('Webcam HD', 'Electronics', 'Accessories', 89.99, 40.00, 'active'),
('Standing Desk', 'Furniture', 'Desks', 599.99, 300.00, 'active');

-- Insert sample orders (last quarter)
INSERT INTO orders (customer_id, order_date, status, total_amount, subtotal, tax_amount, shipping_amount) VALUES
(1, '2024-10-15', 'completed', 1379.97, 1329.98, 39.99, 10.00),
(2, '2024-10-20', 'completed', 899.97, 869.98, 19.99, 10.00),
(3, '2024-11-05', 'completed', 479.98, 449.99, 19.99, 10.00),
(4, '2024-11-10', 'completed', 1729.96, 1699.97, 19.99, 10.00),
(5, '2024-11-15', 'completed', 639.97, 619.98, 9.99, 10.00),
(6, '2024-12-01', 'completed', 229.97, 219.98, 0.00, 10.00),
(7, '2024-12-05', 'completed', 1529.96, 1499.97, 19.99, 10.00),
(8, '2024-12-10', 'completed', 539.97, 529.98, 0.00, 10.00),
(9, '2024-12-15', 'completed', 319.97, 309.98, 0.00, 10.00),
(10, '2024-12-20', 'completed', 729.97, 719.98, 0.00, 10.00);

-- Insert order line items
INSERT INTO order_line_items (order_id, product_id, quantity, price, discount_amount) VALUES
-- Order 1
(1, 1, 1, 1299.99, 0),
(1, 2, 1, 29.99, 0),
-- Order 2
(2, 3, 2, 449.99, 50.00),
-- Order 3
(3, 3, 1, 449.99, 0),
-- Order 4
(4, 1, 1, 1299.99, 0),
(4, 7, 1, 399.99, 0),
-- Order 5
(5, 10, 1, 599.99, 0),
(5, 5, 1, 19.99, 0),
-- Order 6
(6, 4, 2, 79.99, 0),
(6, 5, 3, 19.99, 0),
-- Order 7
(7, 1, 1, 1299.99, 0),
(7, 8, 1, 129.99, 0),
(7, 4, 1, 79.99, 0),
-- Order 8
(8, 3, 1, 449.99, 0),
(8, 4, 1, 79.99, 0),
-- Order 9
(9, 8, 2, 129.99, 0),
(9, 2, 1, 29.99, 20.00),
-- Order 10
(10, 7, 1, 399.99, 0),
(10, 9, 1, 89.99, 0),
(10, 5, 1, 19.99, 0),
(10, 6, 1, 14.99, 0);

INSERT INTO sales_reps (first_name, last_name, email, region, hire_date) VALUES
('Mike', 'Sales', 'mike.sales@company.com', 'North America', '2023-01-15'),
('Sarah', 'Revenue', 'sarah.revenue@company.com', 'Europe', '2023-03-20'),
('Tom', 'Closer', 'tom.closer@company.com', 'Asia', '2023-05-10')
ON CONFLICT (email) DO NOTHING;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_line_items_order_id ON order_line_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_line_items_product_id ON order_line_items(product_id);
CREATE INDEX IF NOT EXISTS idx_customers_region ON customers(region);
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);

-- Grant permissions (for read-only user - optional, create separately for production)
-- CREATE USER readonly_user WITH PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE analytics_db TO readonly_user;
-- GRANT USAGE ON SCHEMA public TO readonly_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;
