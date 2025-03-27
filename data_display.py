import sqlite3
import pandas as pd
from tabulate import tabulate

# Function to display schema and table data nicely formatted
def display_database():
    # Connect to the database
    db_path = "online_sales.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get list of all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    results = {}

    # Helper function to display table data
    def display_table(table_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]

        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        df = pd.DataFrame(rows, columns=columns)
        return df

    # Collect schema information
    schema_info = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        schema_info[table_name] = [{'name': col[1], 'type': col[2], 'primary_key': bool(col[5])} for col in columns]

    results['schema'] = schema_info

    # Collect data for each table
    table_data = {}
    for table in tables:
        table_name = table[0]
        table_data[table_name] = display_table(table_name)

    results['table_data'] = table_data

    # Collect customer orders summary
    cursor.execute("""
    SELECT c.customer_id, c.first_name, c.last_name, c.email, COUNT(o.order_id) as order_count, 
           SUM(o.total_amount) as total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id
    """)
    customer_orders = cursor.fetchall()
    df_customer_orders = pd.DataFrame(customer_orders, 
                                      columns=['customer_id', 'first_name', 'last_name', 'email', 
                                               'order_count', 'total_spent'])

    results['customer_orders_summary'] = df_customer_orders

    # Collect product sales summary
    cursor.execute("""
    SELECT p.product_id, p.name, p.category, p.price, SUM(oi.quantity) as units_sold, 
           SUM(oi.quantity * oi.price_per_unit) as revenue
    FROM products p
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    GROUP BY p.product_id
    ORDER BY revenue DESC
    """)
    product_sales = cursor.fetchall()
    df_product_sales = pd.DataFrame(product_sales, 
                                   columns=['product_id', 'name', 'category', 'price', 
                                            'units_sold', 'revenue'])

    results['product_sales_summary'] = df_product_sales

    # Close connection
    conn.close()

    return results

# Example usage (uncomment the following lines to use directly):
if __name__ == "__main__":
     data = display_database('online_sales.db')
     print(data)
