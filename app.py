from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client
from threading import Timer
import webbrowser


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Twilio API configuration
TWILIO_ACCOUNT_SID = 'ACadd2709df6be8f1dd356df1fa8e526e4'
TWILIO_AUTH_TOKEN = 'c8daa4a1362f7cf8a87d0e414e93e629'
TWILIO_PHONE_NUMBER = '+12107023160'  # Ensure this is in E.164 format

# Scheduler setup
scheduler = BackgroundScheduler()
scheduler.start()

def db_connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="sandeep05",
        database="todo"
    )
def open_browser():
    # Update the path to the Chrome executable as per your system
    chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe %s"
    webbrowser.get(chrome_path).open("http://127.0.0.1:5000")


def send_sms(phone, message):
    print("Send_Sms")
    # Ensure the phone number is in E.164 format
    if not phone.startswith('+'):
        phone = f'+91{phone}'  # Assuming default country code +91 for India
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message_response = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        print(f"Message sent: {message_response.sid}")  # Log message SID for tracking
        
    except Exception as e:
        print(f"Error sending SMS: {e}")

def send_daily_tasks():
   
    conn = db_connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    
    for user in users:
        user_id = user['id']
        phone = user['phone_number']
        print(f"phone:{phone}")
        # Ensure the phone number is in E.164 format
        if not phone.startswith('+'):
            phone = f'+91{phone}'  # Assuming default country code +91 for India

        cursor.execute("SELECT title, due_date FROM tasks WHERE user_id = %s AND DATE(due_date) = CURDATE()", (user_id,))
        tasks = cursor.fetchall()
        
        if tasks:
            task_list = "\n".join([f"{task['title']} - Due: {task['due_date']}" for task in tasks])
            message = f"Hello {user['name']}, here are your tasks for today:\n{task_list}"
            send_sms(phone, message)
    
    cursor.close()
    conn.close()

# Schedule the task to run at 7:00 am daily
scheduler.add_job(send_daily_tasks, 'cron', hour=21, minute=34)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('tasks'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        
        conn = db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['phone'] = user['phone_number']  # Store phone number in session
            return redirect(url_for('tasks'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        phone = request.form['phone']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Connect to the database to check if the phone exists
        conn = db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone,))
        user = cursor.fetchone()
        
        if user:
            # Check if the new password and confirm password match
            if new_password != confirm_password:
                flash("Passwords do not match.", "danger")
            else:
                # Hash the new password and update it in the database
                hashed_password = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password = %s WHERE phone_number = %s", (hashed_password, phone))
                conn.commit()
                flash("Password reset successfully. Please log in with your new password.", "success")
                return redirect(url_for('login'))
        else:
            flash("Phone number not found.", "danger")
        
        cursor.close()
        conn.close()

    return render_template('forgot_password.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        password = generate_password_hash(request.form['password'])
        
        conn = db_connect()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (name, phone_number, password) VALUES (%s, %s, %s)", (name, phone, password))
            conn.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash("Phone number already registered.", "danger")
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():

    conn = db_connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    if 'user_id' not in session:
        return redirect(url_for('login'))
    for user in users:
        user_id = user['id']
        phone = user['phone_number']
        print(f"phone:{phone}")

    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        category = request.form.get('category', 'Other')
        priority = request.form.get('priority', 'Low')
        due_date = request.form.get('due_date', None)

        cursor.execute(
            "INSERT INTO tasks (user_id, title, description, category, priority, due_date) VALUES (%s, %s, %s, %s, %s, %s)",
            (session['user_id'], title, description, category, priority, due_date)
        )
        conn.commit()
        # test_sms()
        # Send SMS notification when a task is added
        #phone = session.get('phone')  # Safely access phone number
        print(phone)
        if phone:  # Ensure it's available
            message = f"New Task Added: {title} - Due: {due_date}"
            send_sms(phone, message)

    cursor.execute("SELECT * FROM tasks WHERE user_id = %s", (session['user_id'],))
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('tasks.html', tasks=tasks, name=session['name'])

@app.route('/tasks/complete/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET completed = TRUE WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('tasks'))

@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('tasks'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(debug=True)