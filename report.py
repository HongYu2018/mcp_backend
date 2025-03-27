import sqlite3
import pandas as pd
from datetime import datetime

def generate_sales_analysis_report(db_path='online_sales.db'):
    """
    Generate a comprehensive sales analysis report from the online sales database.
    Returns the report as a formatted text string.
    """
    # Connect to the database
    conn = sqlite3.connect(db_path)
    
    # Helper function to run SQL queries and return pandas DataFrames
    def run_query(query):
        return pd.read_sql_query(query, conn)
    
    # Start building the report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append(f"ONLINE SALES DATABASE ANALYSIS REPORT")
    report_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    
    # 1. Overall Sales Summary
    report_lines.append("\n1. OVERALL SALES SUMMARY")
    report_lines.append("-" * 30)
    
    # Total orders and revenue
    total_sales = run_query("SELECT COUNT(*) as order_count, SUM(total_amount) as total_revenue FROM orders")
    report_lines.append(f"Total Orders: {total_sales['order_count'].iloc[0]}")
    report_lines.append(f"Total Revenue: ${total_sales['total_revenue'].iloc[0]:.2f}")
    
    # Average order value
    report_lines.append(f"Average Order Value: ${total_sales['total_revenue'].iloc[0] / total_sales['order_count'].iloc[0]:.2f}")
    
    # Order status breakdown
    status_breakdown = run_query("""
        SELECT status, COUNT(*) as count, SUM(total_amount) as total_amount,
        ROUND(AVG(total_amount), 2) as avg_amount
        FROM orders GROUP BY status ORDER BY count DESC
    """)
    
    report_lines.append("\nOrder Status Breakdown:")
    for _, row in status_breakdown.iterrows():
        report_lines.append(f"  {row['status']}: {row['count']} orders, ${row['total_amount']:.2f} total, ${row['avg_amount']} avg")
    
    # 2. Product Analysis
    report_lines.append("\n\n2. PRODUCT ANALYSIS")
    report_lines.append("-" * 30)
    
    # Product count by category
    product_categories = run_query("""
        SELECT category, COUNT(*) as product_count
        FROM products GROUP BY category ORDER BY product_count DESC
    """)
    
    report_lines.append("Product Categories:")
    for _, row in product_categories.iterrows():
        report_lines.append(f"  {row['category']}: {row['product_count']} products")
    
    # Top 5 selling products
    top_products = run_query("""
        SELECT p.name, p.category, p.price,
               SUM(oi.quantity) as units_sold,
               SUM(oi.quantity * oi.price_per_unit) as revenue
        FROM products p
        JOIN order_items oi ON p.product_id = oi.product_id
        GROUP BY p.product_id
        ORDER BY revenue DESC
        LIMIT 5
    """)
    
    report_lines.append("\nTop 5 Products by Revenue:")
    for i, row in top_products.iterrows():
        report_lines.append(f"  {i+1}. {row['name']} ({row['category']})")
        report_lines.append(f"     Price: ${row['price']:.2f} | Units Sold: {row['units_sold']:.0f} | Revenue: ${row['revenue']:.2f}")
    
    # Sales by category
    category_sales = run_query("""
        SELECT p.category, SUM(oi.quantity) as units_sold,
               SUM(oi.quantity * oi.price_per_unit) as revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.category
        ORDER BY revenue DESC
    """)
    
    report_lines.append("\nSales by Category:")
    for _, row in category_sales.iterrows():
        report_lines.append(f"  {row['category']}: {row['units_sold']:.0f} units, ${row['revenue']:.2f} revenue")
    
    # 3. Customer Analysis
    report_lines.append("\n\n3. CUSTOMER ANALYSIS")
    report_lines.append("-" * 30)
    
    # Total customers
    customer_count = run_query("SELECT COUNT(*) as count FROM customers")
    report_lines.append(f"Total Customers: {customer_count['count'].iloc[0]}")
    
    # Top customers by spending
    top_customers = run_query("""
        SELECT c.first_name || ' ' || c.last_name as customer_name,
               COUNT(o.order_id) as order_count,
               SUM(o.total_amount) as total_spent,
               AVG(o.total_amount) as avg_order_value
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id
        ORDER BY total_spent DESC
        LIMIT 5
    """)
    
    report_lines.append("\nTop 5 Customers by Spending:")
    for i, row in top_customers.iterrows():
        report_lines.append(f"  {i+1}. {row['customer_name']}")
        report_lines.append(f"     Orders: {row['order_count']} | Total Spent: ${row['total_spent']:.2f} | Avg Order: ${row['avg_order_value']:.2f}")
    
    # Customer distribution by state
    customer_states = run_query("""
        SELECT state, COUNT(*) as customer_count
        FROM customers
        GROUP BY state
        ORDER BY customer_count DESC
    """)
    
    report_lines.append("\nCustomer Distribution by State:")
    for _, row in customer_states.iterrows():
        report_lines.append(f"  {row['state']}: {row['customer_count']} customers")
    
    # 4. Inventory Status
    report_lines.append("\n\n4. INVENTORY STATUS")
    report_lines.append("-" * 30)
    
    # Inventory overview
    inventory = run_query("""
        SELECT SUM(stock_quantity) as total_units,
               AVG(stock_quantity) as avg_stock,
               MIN(stock_quantity) as min_stock,
               MAX(stock_quantity) as max_stock
        FROM products
    """)
    
    report_lines.append(f"Total Inventory: {inventory['total_units'].iloc[0]:.0f} units")
    report_lines.append(f"Average Stock per Product: {inventory['avg_stock'].iloc[0]:.1f} units")
    report_lines.append(f"Stock Range: {inventory['min_stock'].iloc[0]:.0f} to {inventory['max_stock'].iloc[0]:.0f} units")
    
    # Low stock products
    low_stock = run_query("""
        SELECT name, category, stock_quantity, price
        FROM products
        WHERE stock_quantity < 50
        ORDER BY stock_quantity ASC
    """)
    
    if not low_stock.empty:
        report_lines.append("\nLow Stock Products (less than 50 units):")
        for _, row in low_stock.iterrows():
            report_lines.append(f"  {row['name']} ({row['category']}): {row['stock_quantity']:.0f} units left | ${row['price']:.2f}")
    
    # 5. Payment Method Analysis
    report_lines.append("\n\n5. PAYMENT METHOD ANALYSIS")
    report_lines.append("-" * 30)
    
    payment_methods = run_query("""
        SELECT payment_method, COUNT(*) as order_count, 
               SUM(total_amount) as total_revenue,
               AVG(total_amount) as avg_order_value
        FROM orders
        GROUP BY payment_method
        ORDER BY total_revenue DESC
    """)
    
    report_lines.append("Payment Method Breakdown:")
    for _, row in payment_methods.iterrows():
        percent = (row['order_count'] / total_sales['order_count'].iloc[0]) * 100
        report_lines.append(f"  {row['payment_method']}: {row['order_count']} orders ({percent:.1f}%)")
        report_lines.append(f"     Total Revenue: ${row['total_revenue']:.2f} | Avg Order: ${row['avg_order_value']:.2f}")
    
    # Close the database connection
    conn.close()
    
    # Combine all lines into a single string
    return "\n".join(report_lines)

# Example usage
if __name__ == "__main__":
    report = generate_sales_analysis_report()
    print(report)
    
    # Optionally save to a file
    with open("sales_analysis_report.txt", "w") as f:
        f.write(report)