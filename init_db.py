import sqlite3
from werkzeug.security import generate_password_hash
import json

def init_users_db():
    conn = sqlite3.connect('instance/users.db')
    cursor = conn.cursor()

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

    # Create purchase history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchase_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()

def init_catalog_db():
    conn = sqlite3.connect('instance/catalog.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        image_filename TEXT NOT NULL,
        description TEXT,
        specifications TEXT
    )
    ''')

    # Sample products with detailed specifications
    sample_products = [
        ('Burton Custom X Snowboard', 599.99, 10, 'snowboard_1.jpg',
         'The Burton Custom X is the most aggressive and powerful board in Burton\'s lineup. Perfect for experienced riders.',
         json.dumps({
             'Length': '158cm',
             'Width': '25.6cm',
             'Flex Rating': '8/10',
             'Core Material': 'Dragonfly 600G Carbon',
             'Shape': 'Directional Twin',
             'Terrain': 'All Mountain',
             'Rider Level': 'Advanced/Expert'
         })),
        ('Lib Tech T.Rice Pro Snowboard', 649.99, 8, 'snowboard_2.jpg',
         'The Lib Tech T.Rice Pro is Travis Rice\'s pro model, featuring C2 Technology and environmentally friendly materials.',
         json.dumps({
             'Length': '161.5cm',
             'Width': '25.8cm',
             'Flex Rating': '7/10',
             'Core Material': 'Horsepower Construction',
             'Shape': 'True Twin',
             'Terrain': 'Freestyle/All Mountain',
             'Rider Level': 'Intermediate/Advanced'
         })),
        ('GNU Riders Choice Snowboard', 579.99, 12, 'snowboard_3.jpg',
         'The GNU Riders Choice is a versatile all-mountain board that excels in both park and powder.',
         json.dumps({
             'Length': '157cm',
             'Width': '25.2cm',
             'Flex Rating': '6/10',
             'Core Material': 'Aspen/Paulownia',
             'Shape': 'Directional Twin',
             'Terrain': 'All Mountain/Park',
             'Rider Level': 'Intermediate/Advanced'
         })),
        ('Jones Mountain Twin Snowboard', 549.99, 6, 'snowboard_4.jpg',
         'The Jones Mountain Twin is a high-performance all-mountain board that delivers outstanding versatility and stability.',
         json.dumps({
             'Length': '160cm',
             'Width': '25.4cm',
             'Flex Rating': '7/10',
             'Core Material': 'Bamboo/Paulownia',
             'Shape': 'Directional Twin',
             'Terrain': 'All Mountain',
             'Rider Level': 'Intermediate/Advanced'
         })),
        ('Arbor Architect Snowboard', 599.99, 20, 'snowboard_5.jpg',
         'The Arbor Architect is a premium all-mountain snowboard that combines responsiveness, stability, and sustainability.',
         json.dumps({
             'Length': '159cm',
             'Width': '25.3cm',
             'Flex Rating': '6/10',
             'Core Material': 'Bamboo/Poplar',
             'Shape': 'Directional Twin',
             'Terrain': 'All Mountain',
             'Rider Level': 'Intermediate/Advanced'
         })),
        ('K2 Dynasty Alpine Skis', 499.99, 15, 'ski_1.jpg',
         'The K2 Dynasty is a versatile all-mountain ski that provides excellent performance in various conditions.',
         json.dumps({
             'Length': '170cm',
             'Width': '90mm',
             'Turn Radius': '16m',
             'Core Material': 'Fir/Aspen',
             'Profile': 'All-Terrain Rocker',
             'Terrain': 'All Mountain',
             'Skill Level': 'Intermediate/Advanced'
         })),
        ('Salomon QST 106 Skis', 699.99, 25, 'ski_2.jpg',
         'The Salomon QST 106 is a versatile powder ski that excels in all-mountain conditions.',
         json.dumps({
             'Length': '184cm',
             'Width': '106mm',
             'Turn Radius': '18m',
             'Core Material': 'Poplar/Titanal',
             'Profile': 'Powder Rocker',
             'Terrain': 'All Mountain/Powder',
             'Skill Level': 'Advanced'
         })),
        ('Salomon Stance 96 Skis', 649.99, 30, 'ski_3.jpg',
         'The Salomon Stance 96 is an all-mountain ski that delivers excellent performance on groomed and off-piste terrain.',
         json.dumps({
             'Length': '176cm',
             'Width': '96mm',
             'Turn Radius': '17m',
             'Core Material': 'Poplar/Titanal',
             'Profile': 'All-Terrain Rocker',
             'Terrain': 'All Mountain',
             'Skill Level': 'Intermediate/Advanced'
         })),
        ('Salomon S/Force Bold Skis', 799.99, 40, 'ski_4.jpg',
         'The Salomon S/Force Bold is a high-performance all-mountain ski that delivers exceptional stability and responsiveness.',
         json.dumps({
             'Length': '180cm',
             'Width': '88mm',
             'Turn Radius': '15m',
             'Core Material': 'Poplar/Titanal',
             'Profile': 'All-Terrain Rocker',
             'Terrain': 'All Mountain',
             'Skill Level': 'Advanced'
         }))
    ]

    cursor.executemany('''
    INSERT OR IGNORE INTO products 
    (name, price, stock, image_filename, description, specifications) 
    VALUES (?, ?, ?, ?, ?, ?)
    ''', sample_products)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_users_db()
    init_catalog_db()