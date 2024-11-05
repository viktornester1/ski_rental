# Update init_db.py to handle cart storage
import sqlite3
import json
from werkzeug.security import generate_password_hash

def init_users_db():
    conn = sqlite3.connect('instance/users.db')
    cursor = conn.cursor()

    # Create users table with cart_data column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin BOOLEAN NOT NULL DEFAULT 0,
        cart_data TEXT DEFAULT '{}'
    )
    ''')

    # Add admin user
    admin_password = 'admin123'
    cursor.execute('INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                  ('admin', generate_password_hash(admin_password), True))

    conn.commit()
    conn.close()

#new
def update_users_db():
    conn = sqlite3.connect('instance/users.db')
    cursor = conn.cursor()

    # Add cart_data column
    cursor.execute('''
    ALTER TABLE users ADD COLUMN cart_data TEXT;
    ''')

    conn.commit()
    conn.close()

# Initialize catalog database
def init_catalog_db():
    conn = sqlite3.connect('instance/catalog.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        image_filename TEXT NOT NULL
    )
    ''')

    # Sample products with image filenames
    sample_products = [
        ('Burton Custom X Snowboard', 599.99, 10, 'snowboard_1.jpg'),
        ('Lib Tech T.Rice Pro Snowboard', 649.99, 8, 'snowboard_2.jpg'),
        ('GNU Riders Choice Snowboard', 579.99, 12, 'snowboard_3.jpg'),
        ('Jones Mountain Twin Snowboard', 549.99, 6, 'snowboard_4.jpg'),
        ('Arbor Architect Snowboard', 599.99, 20, 'snowboard_5.jpg'),
        ('K2 Dynasty Alpine Skis', 499.99, 15, 'ski_1.jpg'),
        ('Salomon QST 106 Skis', 699.99, 25, 'ski_2.jpg'),
        ('Salomon Stance 96 Skis', 649.99, 30, 'ski_3.jpg'),
        ('Salomon S/Force Bold Skis', 799.99, 40, 'ski_4.jpg')
    ]

    cursor.executemany('INSERT OR IGNORE INTO products (name, price, stock, image_filename) VALUES (?, ?, ?, ?)',
                      sample_products)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_users_db()
    init_catalog_db()