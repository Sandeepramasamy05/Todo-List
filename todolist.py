from flask import Flask, render_template, request, jsonify
import mysql.connector
import webbrowser
import os
import threading
from datetime import datetime
import pytz

app = Flask(__name__)

# MySQL Configuration
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'root'
MYSQL_DB = 'todo_app'

# Connect to MySQL
def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )

# Initialize the MySQL Database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks
                      (id INT AUTO_INCREMENT PRIMARY KEY, 
                       task VARCHAR(255), 
                       due_date DATE, 
                       priority VARCHAR(50),
                       task_type VARCHAR(50))''')
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to retrieve tasks with optional filtering by task type
@app.route('/get_tasks', methods=['GET'])
def get_tasks():
    task_type = request.args.get('task_type')  
    conn = get_db_connection()
    cursor = conn.cursor()

    if task_type:  
        cursor.execute('SELECT * FROM tasks WHERE task_type = %s ORDER BY FIELD(priority, "High", "Medium", "Low")', (task_type,))
    else:
        cursor.execute('SELECT * FROM tasks ORDER BY FIELD(priority, "High", "Medium", "Low")')  
    
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convert to IST time and return with task information
    ist = pytz.timezone('Asia/Kolkata')
    task_list = []
    for task in tasks:
        task_id, task_name, due_date, priority, task_type = task
        task_list.append((task_id, task_name, due_date, priority, task_type))
    
    return jsonify(task_list)

# API endpoint to add a task
@app.route('/add_task', methods=['POST'])
def add_task():
    task = request.form['task']
    due_date = request.form['due_date']
    priority = request.form['priority']
    task_type = request.form['task_type'] 

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (task, due_date, priority, task_type) VALUES (%s, %s, %s, %s)', 
                   (task, due_date, priority, task_type))  
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(success=True)

# API endpoint to delete a task
@app.route('/delete_task', methods=['POST'])
def delete_task():
    task_id = request.form['id']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(success=True)

# Function to open the browser automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    init_db()  
    app.run(debug=True)
