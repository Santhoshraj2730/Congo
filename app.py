from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")  # Secure secret key

# Database Configuration
db_config = {
    'host': os.getenv("DB_HOST", "localhost"),
    'user': os.getenv("DB_USER", "root"),
    'password': os.getenv("DB_PASSWORD", "Kavi1021"),
    'database': os.getenv("DB_NAME", "ecommerce"),
}

# 🏠 Home Route
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

# 🔍 Search Functionality
@app.route('/search')
def search():
    query = request.args.get('query', '').strip()
    with mysql.connector.connect(**db_config) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM items WHERE name LIKE %s OR description LIKE %s", (f"%{query}%", f"%{query}%"))
        items = cursor.fetchall()
    return render_template('index.html', items=items)

# 📋 Index Page
@app.route('/index')
def index():
    with mysql.connector.connect(**db_config) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM items")
        items = cursor.fetchall()
        cursor.execute("SELECT * FROM items WHERE category = 'phone' LIMIT 4")
        bags = cursor.fetchall()
    return render_template('index.html', items=items, bags=bags)

# 🛍️ Category Filter
@app.route('/category/<string:category_name>')
def category(category_name):
    with mysql.connector.connect(**db_config) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM items WHERE category = %s", (category_name,))
        items = cursor.fetchall()
    return render_template('index.html', items=items)

# 🛒 Add to Cart
@app.route('/add_to_cart/<int:item_id>')
def add_to_cart(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    with mysql.connector.connect(**db_config) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
        item = cursor.fetchone()

        if item:
            cursor.execute("""
                INSERT INTO cart (user_id, item_id, item_name, item_price, quantity)
                VALUES (%s, %s, %s, %s, 1)
            """, (user_id, item['id'], item['name'], item['price']))
            conn.commit()

    return redirect(url_for('view_cart'))

# 🛒 View Cart
@app.route('/view_cart')
def view_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    with mysql.connector.connect(**db_config) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cart WHERE user_id = %s", (user_id,))
        cart_items = cursor.fetchall()

    return render_template('cart.html', cart_items=cart_items)

# 📦 Checkout
@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_name = request.form['user_name']
    user_address = request.form['user_address']
    user_phone = request.form['user_phone']

    with mysql.connector.connect(**db_config) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cart WHERE user_id = %s", (user_id,))
        cart_items = cursor.fetchall()

        for item in cart_items:
            cursor.execute("""
                INSERT INTO orders (item_id, item_name, item_price, quantity, user_name, user_address, user_phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (item['item_id'], item['item_name'], item['item_price'], item['quantity'], user_name, user_address, user_phone))

        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        conn.commit()

    return "<h1>Order placed successfully!</h1><a href='/'>Go Back to Home</a>"

# 🛠️ Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')

# 🔐 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        else:
            return "<h1>Invalid username or password</h1>"

    return render_template('login.html')

# 🔓 Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# 👜 Category Bag Page
@app.route('/category/bag')
def category_bag():
    with mysql.connector.connect(**db_config) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM items WHERE category = %s", ('bag',))
        items = cursor.fetchall()
    return render_template('category_bag.html', items=items)

# 🚀 Run App
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

