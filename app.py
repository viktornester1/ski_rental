from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
import os
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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

#neww
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
    if current_user.is_authenticated:
        return redirect(url_for('catalog'))
    return redirect(url_for('login'))

#new
@app.route('/home')
def home():
    cart = session.get('cart', {})
    total = sum(float(item['price']) * item['quantity'] for item in cart.values()) if cart else 0
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
            return redirect(url_for('catalog'))

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
@login_required
def catalog():
    conn = sqlite3.connect('instance/catalog.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    conn.close()

    cart = session.get('cart', {})
    total = sum(float(item['price']) * item['quantity'] for item in cart.values())

    return render_template('catalog.html',
                           products=products,
                           cart=cart,
                           total=total)


@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
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

        # Generate updated cart HTML
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
    if str(product_id) in cart:
        del cart[str(product_id)]
        session['cart'] = cart
        # Save cart to database after modification
        save_cart_to_db(current_user.id, cart)
    return redirect(url_for('catalog'))


@app.route('/update_product', methods=['POST'])
@admin_required
def update_product():
    product_id = request.form['product_id']
    new_price = request.form['price']
    new_stock = request.form['stock']

    conn = sqlite3.connect('instance/catalog.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET price = ?, stock = ? WHERE id = ?',
                   (new_price, new_stock, product_id))
    conn.commit()
    conn.close()

    flash('Product updated successfully!')
    return redirect(url_for('catalog'))


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

    try:
        # Check stock availability and update stock
        for product_id, item in cart.items():
            cursor_catalog.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
            current_stock = cursor_catalog.fetchone()[0]

            if current_stock < item['quantity']:
                raise Exception(f'Not enough stock available for {item["name"]}')

            # Update stock
            cursor_catalog.execute('''
                UPDATE products 
                SET stock = stock - ? 
                WHERE id = ?
            ''', (item['quantity'], product_id))

            # Record purchase in history
            cursor_users.execute('''
                INSERT INTO purchase_history 
                (user_id, product_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
            ''', (current_user.id, product_id, item['name'],
                  item['quantity'], item['price']))

        conn_catalog.commit()
        conn_users.commit()

        # Clear cart
        session.pop('cart', None)
        save_cart_to_db(current_user.id, {})

        return jsonify({'success': True, 'message': 'Purchase successful!'})

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
        # Calculate cart total
        cart = session.get('cart', {})
        total = sum(float(item['price']) * item['quantity'] for item in cart.values())
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

    conn = sqlite3.connect('instance/users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM purchase_history 
        WHERE user_id = ? 
        ORDER BY purchase_date DESC
    ''', (current_user.id,))
    purchases = cursor.fetchall()
    conn.close()

    # Calculate the total for the cart
    cart = session.get('cart', {})
    total = sum(float(item['price']) * item['quantity'] for item in cart.values())

    return render_template('purchase_history.html', purchases=purchases, total=total)


if __name__ == '__main__':
    app.run(debug=True)