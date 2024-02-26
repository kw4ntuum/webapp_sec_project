from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'votre_clé_secrète'
cwd = __file__.strip('app.py')
DB_PRODUCTS = cwd+'databases\\products.db'
DB_USERS = cwd+'databases\\users.db'
app.jinja_options["autoescape"] = lambda _: False


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Vérifier les informations d'identification de l'utilisateur
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_USERS)
        cursor = conn.cursor()
        command = "SELECT * FROM users WHERE username LIKE '"+ username +"' AND password LIKE '"+password+"'"
        cursor.execute(str(command))
        user = cursor.fetchone()

        if user:
            session['logged_in'] = True
            session['username'] = username
            session['password'] = password
            session['is_admin'] = user[3]
            conn.close()
            return redirect(url_for('stock'))
        else:
            conn.close()
            error = 'Nom d\'utilisateur ou mot de passe incorrect'
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/stock')
def stock():
    # Vérifier si l'utilisateur est connecté
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    else:
        # Récupérer la liste des produits depuis la base de données
        username = session['username']
        conn = sqlite3.connect(DB_PRODUCTS)
        cursor = conn.cursor()
        search_query = request.args.get('search_query')
        if search_query:
            cursor.execute("SELECT * FROM products WHERE nom LIKE ?", ('%' + search_query + '%',))
        else:
            cursor.execute('SELECT * FROM products')
        products = cursor.fetchall()
        # Convertir la liste de tuples en liste de listes
        products = [list(product) for product in products]
        # Fermer la connexion à la base de données
        conn.close()

        return render_template('stock.html', produits=products, search_query=search_query, username=username)

    

@app.route('/ajouter_produit', methods=['GET', 'POST'])
def ajouter_produit():
    # Vérifier si l'utilisateur est connecté
    if 'logged_in' not in session or not session['logged_in'] or session['is_admin']==0:
        return redirect(url_for('stock'))

    if request.method == 'POST':
        nom = request.form['nom']
        quantite = request.form['quantite']
        prix = request.form['prix']
        description = request.form['description']
        # Ajouter le produit à la base de données
        conn = sqlite3.connect(DB_PRODUCTS)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO products (nom, quantite, prix, description) VALUES (?, ?, ?, ?)',
                       (nom, quantite, prix, description))
        conn.commit()
        conn.close()
        return redirect(url_for('stock'))

    return render_template('ajouter_produit.html')

@app.route('/supprimer/<int:produit_id>', methods=['POST'])
def supprimer_produit(produit_id):
    # Vérifier si l'utilisateur est connecté
    if 'logged_in' not in session or not session['logged_in'] or session['is_admin'] == 0:
        return redirect(url_for('stock'))

    # Supprimer le produit de la base de données
    conn = sqlite3.connect(DB_PRODUCTS)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (produit_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('stock'))

@app.route('/modifier/<int:produit_id>', methods=['GET', 'POST'])
def modifier_produit(produit_id):
    # Vérifier si l'utilisateur est connecté
    if 'logged_in' not in session or not session['logged_in'] or session['is_admin'] == 0:
        return redirect(url_for('stock'))

    if request.method == 'POST':
        nom = request.form['nom']
        quantite = request.form['quantite']
        prix = request.form['prix']
        description = request.form['description']
        # Mettre à jour les informations du produit dans la base de données
        conn = sqlite3.connect(DB_PRODUCTS)
        cursor = conn.cursor()
        cursor.execute('UPDATE products SET nom = ?, quantite = ?, prix = ?, description = ? WHERE id = ?',
                       (nom, quantite, prix, description, produit_id))
        conn.commit()
        conn.close()
        return redirect(url_for('stock'))
    if request.method == 'GET':
        conn = sqlite3.connect(DB_PRODUCTS)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE id = ?', (produit_id,))
        produit = cursor.fetchone()
        conn.close()

    # Récupérer les informations du produit depuis la base de données
    conn = sqlite3.connect(DB_PRODUCTS)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (produit_id,))
    produit = cursor.fetchone()
    conn.close()

    return render_template('modifier.html', produit=produit)


if __name__ == '__main__':
    app.run(debug=False)

