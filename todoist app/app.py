from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
import re
from config import db_config

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config.update(db_config)

mysql = MySQL(app)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        password = request.form['password']

        if not re.match(r'^[0-9]{10}$', phone):
            flash('Phone number must be 10 digits.')
            return redirect(url_for('register'))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, phone, password) VALUES (%s, %s, %s)", (name, phone, password))
        mysql.connection.commit()
        cur.close()
        flash('Registration successful!')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE phone = %s AND password = %s", (phone, password))
        user = cur.fetchone()
        cur.close()

        if user:
            flash('Login successful!')
            return redirect(url_for('home'))
        else:
            flash('Invalid phone number or password.')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        phone = request.form['phone']
        new_password = request.form['new_password']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password = %s WHERE phone = %s", (new_password, phone))
        mysql.connection.commit()
        cur.close()

        flash('Password updated successfully!')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/home')
def home():
    return "Welcome to the Home Page!"

if __name__ == '__main__':
    app.run(debug=True)
