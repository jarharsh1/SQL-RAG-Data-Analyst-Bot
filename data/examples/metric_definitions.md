# Metric Definitions

Official definitions for business metrics used in analytics.

## Revenue Metrics

### Revenue
- **Formula**: `SUM(order_line_items.price * order_line_items.quantity)`
- **Source Table**: `order_line_items`
- **Grain**: `order_id`
- **Default Filters**: `orders.status != 'cancelled'`
- **Description**: Total revenue from all completed orders, excluding cancelled orders

### Gross Revenue
- **Formula**: `SUM(order_line_items.price * order_line_items.quantity)`
- **Source Table**: `order_line_items`
- **Grain**: `order_id`
- **Default Filters**: None
- **Description**: Total revenue including all orders regardless of status

### Net Revenue
- **Formula**: `SUM(order_line_items.price * order_line_items.quantity) - SUM(refunds.amount)`
- **Source Table**: `order_line_items`, `refunds`
- **Grain**: `order_id`
- **Default Filters**: `orders.status = 'completed'`
- **Description**: Revenue after refunds

## Customer Metrics

### Active Customers
- **Formula**: `COUNT(DISTINCT customers.customer_id)`
- **Source Table**: `customers`
- **Grain**: `customer_id`
- **Default Filters**: `customers.status = 'active'`
- **Description**: Number of active customer accounts

### New Customers
- **Formula**: `COUNT(DISTINCT customers.customer_id)`
- **Source Table**: `customers`
- **Grain**: `customer_id`
- **Default Filters**: `customers.created_at >= [start_date]`
- **Description**: Number of customers acquired in the specified period

### Customer Lifetime Value (CLV)
- **Formula**: `SUM(orders.total_amount) / COUNT(DISTINCT customers.customer_id)`
- **Source Table**: `orders`, `customers`
- **Grain**: `customer_id`
- **Default Filters**: `orders.status = 'completed'`
- **Description**: Average total revenue per customer

## Order Metrics

### Order Count
- **Formula**: `COUNT(DISTINCT orders.order_id)`
- **Source Table**: `orders`
- **Grain**: `order_id`
- **Default Filters**: None
- **Description**: Total number of orders

### Completed Orders
- **Formula**: `COUNT(DISTINCT orders.order_id)`
- **Source Table**: `orders`
- **Grain**: `order_id`
- **Default Filters**: `orders.status = 'completed'`
- **Description**: Number of successfully completed orders

### Average Order Value (AOV)
- **Formula**: `SUM(orders.total_amount) / COUNT(DISTINCT orders.order_id)`
- **Source Table**: `orders`
- **Grain**: `order_id`
- **Default Filters**: `orders.status = 'completed'`
- **Description**: Average revenue per order

## Product Metrics

### Units Sold
- **Formula**: `SUM(order_line_items.quantity)`
- **Source Table**: `order_line_items`
- **Grain**: `product_id`
- **Default Filters**: `orders.status = 'completed'`
- **Description**: Total number of product units sold

### Product Revenue
- **Formula**: `SUM(order_line_items.price * order_line_items.quantity)`
- **Source Table**: `order_line_items`
- **Grain**: `product_id`
- **Default Filters**: `orders.status = 'completed'`
- **Description**: Total revenue by product

## Time-Based Metrics

### Monthly Recurring Revenue (MRR)
- **Formula**: `SUM(subscriptions.monthly_amount)`
- **Source Table**: `subscriptions`
- **Grain**: `subscription_id`
- **Default Filters**: `subscriptions.status = 'active'`
- **Description**: Total recurring revenue per month from active subscriptions

### Churn Rate
- **Formula**: `COUNT(DISTINCT cancelled_customers) / COUNT(DISTINCT total_customers)`
- **Source Table**: `customers`
- **Grain**: `customer_id`
- **Default Filters**: Date range specific
- **Description**: Percentage of customers who cancelled in the period
