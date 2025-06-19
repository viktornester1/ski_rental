from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
import os
import json
from datetime import datetime
import pytz
from chatbot import chatbot_bp
from chatbot.rag_utils import RAGHelper
import threading

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Register chatbot blueprint
app.register_blueprint(chatbot_bp)

# Initialize RAG helper for stock updates
rag_helper = RAGHelper()

# Ensure upload folder exists
UPLOAD_FOLDER = 'static/images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


class User(UserMixin):
    def __init__(self, id, username, is_admin=False):
        self.id = id
        self.username = username
        self.is_admin = is_admin


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function

def load_cart_from_db(user_id):
    conn = sqlite3.connect('instance/users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT cart_data FROM users WHERE id = ?', (user_id,))
    cart_data = cursor.fetchone()
    conn.close()

    if cart_data and cart_data[0]:
        return json.loads(cart_data[0])
    return {}


def save_cart_to_db(user_id, cart):
    conn = sqlite3.connect('instance/users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET cart_data = ? WHERE id = ?',
                   (json.dumps(cart), user_id))
    conn.commit()
    conn.close()

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('instance/users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, is_admin FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None


@app.route('/')
def index():
    return redirect(url_for('catalog'))

def calculate_cart_total(cart):
    return sum(float(item['price']) * item['quantity'] for item in cart.values()) if cart else 0

@app.route('/home')
def home():
    cart = session.get('cart', {})
    total = calculate_cart_total(cart)
    return render_template('home.html', total=total)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin':
            flash('Username "admin" is reserved.')
            return redirect(url_for('register'))

        conn = sqlite3.connect('instance/users.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            flash('Username already exists.')
            conn.close()
            return redirect(url_for('register'))

        cursor.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                       (username, generate_password_hash(password), False))
        conn.commit()
        conn.close()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('instance/users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], user_data[1], user_data[3])
            login_user(user)

            # Load cart from database into session
            session['cart'] = load_cart_from_db(user.id)
            
            # Get the next parameter or default to catalog
            next_page = request.args.get('next') or url_for('catalog')
            return redirect(next_page)

        flash('Invalid username or password')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    if not current_user.is_admin:
        # Save cart to database before clearing session
        save_cart_to_db(current_user.id, session.get('cart', {}))
    session.pop('cart', None)
    logout_user()
    return redirect(url_for('login'))


@app.route('/catalog')
def catalog():
    conn = sqlite3.connect('instance/catalog.db')
    cursor = conn.cursor()
    
    # Get filter parameter from query string
    equipment_type = request.args.get('type', '')
    
    if equipment_type:
        # Filter products based on equipment type
        if equipment_type == 'ski':
            cursor.execute('SELECT * FROM products WHERE name LIKE ?', ('%Skis%',))
        elif equipment_type == 'snowboard':
            cursor.execute('SELECT * FROM products WHERE name LIKE ?', ('%Snowboard%',))
        else:
            cursor.execute('SELECT * FROM products')
    else:
        cursor.execute('SELECT * FROM products')
        
    products = cursor.fetchall()
    conn.close()

    cart = session.get('cart', {}) if current_user.is_authenticated else {}
    total = calculate_cart_total(cart) if current_user.is_authenticated else 0

    return render_template('catalog.html',
                         products=products,
                         cart=cart,
                         total=total,
                         current_filter=equipment_type)


@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'message': 'Please log in or register to add items to your cart.',
            'redirect': url_for('login')
        })

    if current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admins cannot add items to cart.'})

    conn = sqlite3.connect('instance/catalog.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    conn.close()

    if product:
        cart = session.get('cart', {})
        product_id_str = str(product_id)

        if product_id_str in cart:
            if cart[product_id_str]['quantity'] < product[3]:  # Check stock
                cart[product_id_str]['quantity'] += 1
            else:
                return jsonify({'success': False, 'message': 'No more stock available'})
        else:
            if product[3] > 0:  # Check stock
                cart[product_id_str] = {
                    'name': product[1],
                    'price': product[2],
                    'quantity': 1
                }

        session['cart'] = cart
        save_cart_to_db(current_user.id, cart)

        cart_html = render_template('cart_items.html',
                                 cart=cart,
                                 total=sum(float(item['price']) * item['quantity'] for item in cart.values()))

        return jsonify({
            'success': True,
            'cart_count': len(cart),
            'cart_html': cart_html
        })

    return jsonify({'success': False, 'message': 'Product not found'})

@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        del cart[product_id_str]
        session['cart'] = cart
        save_cart_to_db(current_user.id, cart)
        total = sum(float(item['price']) * item['quantity'] for item in cart.values())
        cart_html = render_template('cart_items.html',
                                  cart=cart,
                                  total=total)
        return jsonify({
            'success': True,
            'cart_count': len(cart),
            'cart_html': cart_html
        })
    return jsonify({
        'success': False,
        'message': 'Product not found in cart'
    })

@app.route('/decrement_from_cart/<int:product_id>')
@login_required
def decrement_from_cart(product_id):
    cart = session.get('cart', {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        if cart[product_id_str]['quantity'] > 1:
            cart[product_id_str]['quantity'] -= 1
        else:
            del cart[product_id_str]
        session['cart'] = cart
        save_cart_to_db(current_user.id, cart)
        total = sum(float(item['price']) * item['quantity'] for item in cart.values())
        cart_html = render_template('cart_items.html', cart=cart, total=total)
        return jsonify({
            'success': True,
            'cart_count': len(cart),
            'cart_html': cart_html
        })
    return jsonify({'success': False, 'message': 'Product not found in cart'})

@app.route('/update_product', methods=['POST'])
@admin_required
def update_product():
    try:
        # Check if request is JSON
        if request.is_json:
            data = request.get_json()
            product_id = data.get('product_id')
            new_price = data.get('price')
            new_stock = data.get('stock')
        else:
            # For backward compatibility, also handle form data
            product_id = request.form['product_id']
            new_price = request.form['price']
            new_stock = request.form['stock']
        
        conn = sqlite3.connect('instance/catalog.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE products SET price = ?, stock = ? WHERE id = ?',
                    (new_price, new_stock, product_id))
        conn.commit()
        conn.close()
        
        # If it's an AJAX request, return JSON
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Product updated successfully!',
                'product': {
                    'id': product_id,
                    'price': new_price,
                    'stock': new_stock
                }
            })
        
        # Otherwise, redirect for traditional form submit
        flash('Product updated successfully!')
        return redirect(url_for('catalog'))
    except Exception as e:
        if request.is_json:
            return jsonify({
                'success': False,
                'message': f'Error updating product: {str(e)}'
            })
        flash(f'Error updating product: {str(e)}')
        return redirect(url_for('catalog'))

def update_rag_embeddings_async():
    """Update RAG embeddings in a background thread"""
    try:
        rag_helper.clear_embeddings()
    except Exception as e:
        print(f"Error updating RAG embeddings: {str(e)}")

@app.route('/buy_products', methods=['POST'])
@login_required
def buy_products():
    if current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admins cannot make purchases.'})

    cart = session.get('cart', {})
    if not cart:
        return jsonify({'success': False, 'message': 'Your cart is empty.'})

    conn_catalog = sqlite3.connect('instance/catalog.db')
    conn_users = sqlite3.connect('instance/users.db')
    cursor_catalog = conn_catalog.cursor()
    cursor_users = conn_users.cursor()

    updated_products = []

    try:
        for product_id, item in cart.items():
            cursor_catalog.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
            current_stock = cursor_catalog.fetchone()[0]

            if current_stock < item['quantity']:
                raise Exception(f'Not enough stock available for {item["name"]}')
            new_stock = current_stock - item['quantity']
            cursor_catalog.execute('''
                UPDATE products 
                SET stock = ? 
                WHERE id = ?
            ''', (new_stock, product_id))
            updated_products.append({
                'id': product_id,
                'stock': new_stock
            })
            cursor_users.execute('''
                INSERT INTO purchase_history 
                (user_id, product_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
            ''', (current_user.id, product_id, item['name'],
                  item['quantity'], item['price']))

        conn_catalog.commit()
        conn_users.commit()
        session.pop('cart', None)
        
        # Update RAG embeddings in background
        thread = threading.Thread(target=update_rag_embeddings_async)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Purchase successful!',
            'updated_products': updated_products
        })

    except Exception as e:
        conn_catalog.rollback()
        conn_users.rollback()
        return jsonify({'success': False, 'message': str(e)})

    finally:
        conn_catalog.close()
        conn_users.close()


@app.route('/product/<int:product_id>')
def product_details(product_id):
    conn = sqlite3.connect('instance/catalog.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    conn.close()

    if product:
        specifications = json.loads(product[6]) if product[6] else {}
        cart = session.get('cart', {}) if current_user.is_authenticated else {}
        total = calculate_cart_total(cart) if current_user.is_authenticated else 0
        return render_template('product_details.html',
                             product=product,
                             specifications=specifications,
                             total=total)
    return redirect(url_for('catalog'))


@app.route('/purchase_history')
@login_required
def purchase_history():
    if current_user.is_admin:
        return redirect(url_for('catalog'))

    conn_users = sqlite3.connect('instance/users.db')
    cursor_users = conn_users.cursor()
    cursor_users.execute('''
        SELECT * FROM purchase_history 
        WHERE user_id = ? 
        ORDER BY purchase_date DESC
    ''', (current_user.id,))
    purchases = cursor_users.fetchall()
    conn_users.close()

    conn_catalog = sqlite3.connect('instance/catalog.db')
    cursor_catalog = conn_catalog.cursor()
    purchases_with_images = []
    kyiv_tz = pytz.timezone('Europe/Kiev')
    for purchase in purchases:
        purchase_list = list(purchase)
        # Get image filename from products table
        cursor_catalog.execute('SELECT image_filename FROM products WHERE id = ?', (purchase[2],))
        result = cursor_catalog.fetchone()
        image_filename = result[0] if result else 'placeholder.jpg'
        purchase_list.append(image_filename)
        # Convert date to Kyiv timezone
        if isinstance(purchase_list[6], str):
            dt = datetime.strptime(purchase_list[6], '%Y-%m-%d %H:%M:%S')
            dt = pytz.utc.localize(dt).astimezone(kyiv_tz)
            purchase_list[6] = dt
        purchases_with_images.append(tuple(purchase_list))
    conn_catalog.close()

    cart = session.get('cart', {})
    total = calculate_cart_total(cart)

    return render_template('purchase_history.html', purchases=purchases_with_images, total=total)

if __name__ == '__main__':
    app.run(debug=True)
