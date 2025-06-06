from flask import jsonify, Flask, render_template, request, redirect, url_for, session,flash
import sqlite3
import os


app = Flask(__name__)
app.secret_key = 'secretkey'

DATABASE = os.path.join(app.root_path, 'database', 'ecomponents.db')

def init_db():
    conn = get_db_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/product/<int:product_id>')
def product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    return render_template('product.html', product=product)

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product:
        cart = session.get('cart', [])
        for item in cart:
            if item['id'] == product['id']:
                item['quantity'] += 1
                break
        else:
            cart.append({'id': product['id'], 'name': product['name'], 'price': product['price'], 'quantity': 1})
        session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', [])
    cart = [item for item in cart if item['id'] != product_id]
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()

        users=conn.execute("SELECT * FROM users WHERE username == ?",(username,)).fetchall()
        if users!=[]:
            flash("Данный логин уже занят")
            return redirect(url_for("register"))
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неверные данные')
    return render_template('login.html')


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    filter_text = request.args.get('filter', '')
    conn = get_db_connection()
    if filter_text:
        orders = conn.execute(
            "SELECT * FROM orders WHERE user_id = ? AND product_name LIKE ? ORDER BY date DESC",
            (session['user_id'], f'%{filter_text}%')
        ).fetchall()
    else:
        orders = conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY date DESC",
            (session['user_id'],)
        ).fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)


@app.route('/suggest')
def suggest():
    q = request.args.get('q', '')
    conn = get_db_connection()
    results = conn.execute("SELECT name FROM products WHERE name LIKE ? LIMIT 10", (f"%{q}%",)).fetchall()
    conn.close()
    return jsonify([row['name'] for row in results])


@app.route('/delivery')
def delivery():
    return render_template('delivery.html')


@app.route('/howto')
def howto():
    return render_template('howto.html')



@app.route('/compare/add/<int:product_id>', methods=['POST'])
def compare_add(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product:
        compare_list = session.get('compare', [])
        if product['id'] not in [item['id'] for item in compare_list]:
            compare_list.append({'id': product['id'], 'name': product['name'], 'description': product['description'], 'price': product['price']})
        session['compare'] = compare_list
    return redirect(url_for('compare'))

@app.route('/compare')
def compare():
    items = session.get('compare', [])
    return render_template('compare.html', items=items)

@app.route('/compare/remove/<int:product_id>', methods=['POST'])
def remove_compare(product_id):
    compare_list = session.get('compare', [])
    compare_list = [item for item in compare_list if item['id'] != product_id]
    session['compare'] = compare_list
    return redirect(url_for('compare'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    return render_template('chekout.html')

@app.route('/catalog')
def catalog():
    category = request.args.get('category')
    filter_text = request.args.get('filter')
    conn = get_db_connection()
    query = "SELECT * FROM products"
    params = []

    if category:
        query += " WHERE category = ?"
        params.append(category)
    elif filter_text:
        query += " WHERE name LIKE ? OR description LIKE ?"
        params.extend([f"%{filter_text}%", f"%{filter_text}%"])

    products = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT DISTINCT category FROM products").fetchall()
    conn.close()
    return render_template('catalog.html', products=products, categories=categories, selected_category=category)

init_db()

if __name__ == '__main__':
    app.run(debug=True)

