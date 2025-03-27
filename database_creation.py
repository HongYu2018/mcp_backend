import sqlite3
import datetime
import random

# Connect to SQLite database (creates it if it doesn't exist)
conn = sqlite3.connect('online_sales.db')
cursor = conn.cursor()

# Create customers table
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    zipcode TEXT,
    registration_date TEXT NOT NULL,
    last_login TEXT
)
''')

# Create products table
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock_quantity INTEGER NOT NULL,
    created_date TEXT NOT NULL
)
''')

# Create orders table
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    total_amount REAL NOT NULL,
    status TEXT NOT NULL,
    shipping_address TEXT,
    payment_method TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
)
''')

# Create order_items table
cursor.execute('''
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price_per_unit REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (order_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
)
''')

# Sample data for customers
customers = [
    ('John', 'Smith', 'john.smith@email.com', '123 Main St', 'New York', 'NY', '10001', 
     '2023-01-15', '2024-03-10'),
    ('Jane', 'Doe', 'jane.doe@email.com', '456 Oak Ave', 'Los Angeles', 'CA', '90001', 
     '2023-02-20', '2024-03-12'),
    ('Michael', 'Johnson', 'michael.j@email.com', '789 Pine Blvd', 'Chicago', 'IL', '60007', 
     '2023-03-05', '2024-03-09'),
    ('Emily', 'Williams', 'emily.w@email.com', '321 Cedar Dr', 'Houston', 'TX', '77001', 
     '2023-04-10', '2024-03-11'),
    ('David', 'Brown', 'david.b@email.com', '654 Maple Ln', 'Phoenix', 'AZ', '85001', 
     '2023-05-22', '2024-03-08')
]

# Insert customers
cursor.executemany('''
INSERT INTO customers (first_name, last_name, email, address, city, state, zipcode, 
                      registration_date, last_login)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', customers)

# Sample data for products
products = [
    ('Laptop Pro', 'High-end laptop with 16GB RAM and 512GB SSD', 'Electronics', 1299.99, 50, '2023-01-10'),
    ('Smartphone X', 'Latest smartphone with dual camera', 'Electronics', 799.99, 100, '2023-02-05'),
    ('Cotton T-Shirt', 'Comfortable cotton t-shirt, various colors', 'Clothing', 19.99, 200, '2023-01-20'),
    ('Chef Knife Set', 'Professional 5-piece knife set', 'Kitchen', 89.99, 30, '2023-03-15'),
    ('Wireless Headphones', 'Noise-cancelling wireless headphones', 'Electronics', 159.99, 75, '2023-02-25'),
    ('Yoga Mat', 'Non-slip exercise yoga mat', 'Sports', 29.99, 120, '2023-04-05'),
    ('Coffee Maker', 'Programmable coffee maker with timer', 'Kitchen', 49.99, 60, '2023-03-20'),
    ('Running Shoes', 'Lightweight running shoes for all terrains', 'Footwear', 79.99, 90, '2023-05-01')
]

# Insert products
cursor.executemany('''
INSERT INTO products (name, description, category, price, stock_quantity, created_date)
VALUES (?, ?, ?, ?, ?, ?)
''', products)

# Generate some random orders
orders = []
order_items = []
order_id = 1
order_item_id = 1

# Generate orders for each customer
for customer_id in range(1, 6):
    # Each customer has 1-3 orders
    for _ in range(random.randint(1, 3)):
        order_date = datetime.datetime(2024, random.randint(1, 3), random.randint(1, 28)).strftime('%Y-%m-%d')
        total_amount = 0
        status = random.choice(['Pending', 'Shipped', 'Delivered', 'Cancelled'])
        payment_method = random.choice(['Credit Card', 'PayPal', 'Apple Pay', 'Google Pay'])
        
        # Get customer address information for shipping
        cursor.execute("SELECT address, city, state, zipcode FROM customers WHERE customer_id = ?", (customer_id,))
        customer_info = cursor.fetchone()
        shipping_address = f"{customer_info[0]}, {customer_info[1]}, {customer_info[2]} {customer_info[3]}"
        
        orders.append((customer_id, order_date, 0, status, shipping_address, payment_method))
        
        # Generate 1-5 items per order
        num_items = random.randint(1, 5)
        # Get random products without repetition
        product_ids = random.sample(range(1, 9), num_items)
        
        for product_id in product_ids:
            # Get product price
            cursor.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
            price = cursor.fetchone()[0]
            
            quantity = random.randint(1, 3)
            item_total = price * quantity
            total_amount += item_total
            
            order_items.append((order_id, product_id, quantity, price))
            order_item_id += 1
        
        # Update order with correct total
        orders[-1] = (customer_id, order_date, total_amount, status, shipping_address, payment_method)
        order_id += 1

# Insert orders
cursor.executemany('''
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address, payment_method)
VALUES (?, ?, ?, ?, ?, ?)
''', orders)

# Insert order items
cursor.executemany('''
INSERT INTO order_items (order_id, product_id, quantity, price_per_unit)
VALUES (?, ?, ?, ?)
''', order_items)

# Commit changes and close connection
conn.commit()
conn.close()

print("Database created successfully with sample data!")