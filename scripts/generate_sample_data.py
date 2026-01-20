#!/usr/bin/env python3
"""
Sample Data Generator - Creates realistic CSV files for demo purposes.

This generates CSV files with sample business data that can be queried
without needing a database. Perfect for demos and testing.

Usage:
    python scripts/generate_sample_data.py
    python scripts/generate_sample_data.py --output-dir data/csv --num-customers 100
"""

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Sample data pools
FIRST_NAMES = [
    "John", "Jane", "Bob", "Alice", "Charlie", "Diana", "Edward", "Fiona",
    "George", "Helen", "Ian", "Julia", "Kevin", "Laura", "Michael", "Nancy",
    "Oliver", "Patricia", "Quinn", "Rachel", "Steven", "Teresa", "Victor", "Wendy"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White"
]

REGIONS = ["North America", "Europe", "Asia", "South America"]

COUNTRIES = {
    "North America": ["USA", "Canada", "Mexico"],
    "Europe": ["UK", "Germany", "France", "Spain", "Italy"],
    "Asia": ["Japan", "China", "India", "South Korea", "Singapore"],
    "South America": ["Brazil", "Argentina", "Chile", "Colombia"]
}

PRODUCT_NAMES = [
    "Laptop Pro 15\"", "Laptop Pro 13\"", "Desktop Workstation", "Tablet 10\"",
    "Wireless Mouse", "Wireless Keyboard", "USB-C Cable", "USB Hub",
    "Monitor 27\"", "Monitor 24\"", "Webcam HD", "Webcam 4K",
    "Office Chair Premium", "Office Chair Standard", "Standing Desk", "Desk Standard",
    "Desk Lamp LED", "Floor Lamp", "Bookshelf", "File Cabinet",
    "Notebook Set", "Pen Set", "Sticky Notes", "Folder Set",
    "Printer Laser", "Printer Inkjet", "Scanner", "Shredder"
]

CATEGORIES = {
    "Electronics": ["Computers", "Accessories", "Displays", "Audio/Video"],
    "Furniture": ["Chairs", "Desks", "Lighting", "Storage"],
    "Office Supplies": ["Paper", "Writing", "Organization", "Filing"],
    "Peripherals": ["Input Devices", "Cables", "Hubs", "Adapters"]
}

ORDER_STATUSES = ["pending", "completed", "shipped", "cancelled", "refunded"]


def generate_customers(num_customers: int) -> List[Dict[str, Any]]:
    """Generate sample customer data."""
    customers = []

    for i in range(1, num_customers + 1):
        region = random.choice(REGIONS)
        country = random.choice(COUNTRIES[region])
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        customer = {
            "customer_id": i,
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
            "first_name": first_name,
            "last_name": last_name,
            "region": region,
            "country": country,
            "status": random.choice(["active", "active", "active", "inactive"]),  # 75% active
            "signup_date": (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d"),
            "total_orders": 0,  # Will be updated later
            "lifetime_value": 0.0  # Will be updated later
        }
        customers.append(customer)

    return customers


def generate_products(num_products: int = 50) -> List[Dict[str, Any]]:
    """Generate sample product data."""
    products = []
    product_names = PRODUCT_NAMES.copy()

    # Generate more products if needed
    while len(product_names) < num_products:
        product_names.append(f"Product {len(product_names) + 1}")

    for i in range(1, num_products + 1):
        category = random.choice(list(CATEGORIES.keys()))
        subcategory = random.choice(CATEGORIES[category])

        # Realistic pricing based on category
        if category == "Electronics":
            unit_price = round(random.uniform(29.99, 1499.99), 2)
        elif category == "Furniture":
            unit_price = round(random.uniform(79.99, 799.99), 2)
        else:
            unit_price = round(random.uniform(9.99, 99.99), 2)

        cost = round(unit_price * random.uniform(0.4, 0.7), 2)

        product = {
            "product_id": i,
            "product_name": product_names[i - 1] if i <= len(product_names) else f"Product {i}",
            "category": category,
            "subcategory": subcategory,
            "unit_price": unit_price,
            "cost": cost,
            "margin": round(((unit_price - cost) / unit_price) * 100, 2),
            "status": random.choice(["active", "active", "active", "discontinued"]),
            "stock_quantity": random.randint(0, 500),
            "reorder_level": random.randint(10, 50)
        }
        products.append(product)

    return products


def generate_orders(customers: List[Dict], products: List[Dict], num_orders: int) -> tuple:
    """Generate sample orders and order line items."""
    orders = []
    line_items = []
    line_item_id = 1

    # Generate orders over the last year
    start_date = datetime.now() - timedelta(days=365)

    for i in range(1, num_orders + 1):
        customer = random.choice(customers)
        order_date = start_date + timedelta(days=random.randint(0, 365))

        # Determine order status (90% completed)
        status = random.choices(
            ORDER_STATUSES,
            weights=[5, 80, 5, 7, 3],
            k=1
        )[0]

        # Generate 1-5 line items per order
        num_items = random.randint(1, 5)
        order_items = random.sample(products, min(num_items, len(products)))

        subtotal = 0.0

        # Generate line items
        for product in order_items:
            quantity = random.randint(1, 5)
            price = product["unit_price"]
            discount = round(random.choice([0, 0, 0, 0.1, 0.15, 0.2]) * price * quantity, 2)
            line_total = round(price * quantity - discount, 2)

            line_item = {
                "line_item_id": line_item_id,
                "order_id": i,
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "quantity": quantity,
                "unit_price": price,
                "discount_amount": discount,
                "line_total": line_total
            }
            line_items.append(line_item)
            subtotal += line_total
            line_item_id += 1

        tax_amount = round(subtotal * 0.08, 2)  # 8% tax
        shipping_amount = 10.0 if subtotal < 100 else 0.0  # Free shipping over $100
        total_amount = round(subtotal + tax_amount + shipping_amount, 2)

        order = {
            "order_id": i,
            "customer_id": customer["customer_id"],
            "customer_email": customer["email"],
            "order_date": order_date.strftime("%Y-%m-%d"),
            "order_quarter": f"Q{(order_date.month - 1) // 3 + 1}",
            "order_year": order_date.year,
            "status": status,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "shipping_amount": shipping_amount,
            "total_amount": total_amount,
            "num_items": num_items,
            "region": customer["region"],
            "country": customer["country"]
        }
        orders.append(order)

        # Update customer metrics
        if status == "completed":
            customer["total_orders"] += 1
            customer["lifetime_value"] += total_amount

    return orders, line_items


def generate_sales_reps(num_reps: int = 10) -> List[Dict[str, Any]]:
    """Generate sample sales representative data."""
    reps = []

    for i in range(1, num_reps + 1):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        region = random.choice(REGIONS)
        hire_date = datetime.now() - timedelta(days=random.randint(90, 1825))

        rep = {
            "rep_id": i,
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name.lower()}.{last_name.lower()}@company.com",
            "region": region,
            "hire_date": hire_date.strftime("%Y-%m-%d"),
            "tenure_days": (datetime.now() - hire_date).days,
            "status": random.choice(["active", "active", "active", "on_leave"])
        }
        reps.append(rep)

    return reps


def write_csv(data: List[Dict], filename: str, output_dir: Path) -> None:
    """Write data to CSV file."""
    if not data:
        print(f"Warning: No data to write for {filename}")
        return

    filepath = output_dir / filename

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    print(f"✓ Created {filename} ({len(data)} rows)")


def main():
    """Generate all sample CSV files."""
    parser = argparse.ArgumentParser(description="Generate sample CSV data")
    parser.add_argument(
        "--output-dir",
        default="data/csv",
        help="Output directory for CSV files"
    )
    parser.add_argument(
        "--num-customers",
        type=int,
        default=100,
        help="Number of customers to generate"
    )
    parser.add_argument(
        "--num-products",
        type=int,
        default=50,
        help="Number of products to generate"
    )
    parser.add_argument(
        "--num-orders",
        type=int,
        default=500,
        help="Number of orders to generate"
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Generating Sample CSV Data")
    print("=" * 60)

    # Generate data
    print("\nGenerating customers...")
    customers = generate_customers(args.num_customers)

    print("Generating products...")
    products = generate_products(args.num_products)

    print("Generating orders and line items...")
    orders, line_items = generate_orders(customers, products, args.num_orders)

    print("Generating sales representatives...")
    sales_reps = generate_sales_reps()

    # Update customer lifetime values
    for customer in customers:
        customer["lifetime_value"] = round(customer["lifetime_value"], 2)

    # Write CSV files
    print("\nWriting CSV files...")
    write_csv(customers, "customers.csv", output_dir)
    write_csv(products, "products.csv", output_dir)
    write_csv(orders, "orders.csv", output_dir)
    write_csv(line_items, "order_line_items.csv", output_dir)
    write_csv(sales_reps, "sales_reps.csv", output_dir)

    # Generate summary
    total_revenue = sum(o["total_amount"] for o in orders if o["status"] == "completed")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Customers: {len(customers)}")
    print(f"Products: {len(products)}")
    print(f"Orders: {len(orders)}")
    print(f"  - Completed: {sum(1 for o in orders if o['status'] == 'completed')}")
    print(f"  - Cancelled: {sum(1 for o in orders if o['status'] == 'cancelled')}")
    print(f"Line Items: {len(line_items)}")
    print(f"Sales Reps: {len(sales_reps)}")
    print(f"Total Revenue: ${total_revenue:,.2f}")
    print("\n✓ Sample data generation complete!")
    print("\nNext steps:")
    print("1. Run: python scripts/init_csv_metadata.py")
    print("2. Set DATABASE_TYPE=csv in .env")
    print("3. Start the application")


if __name__ == "__main__":
    main()
