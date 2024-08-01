from flask import Flask, request, render_template, redirect, url_for, session
from flask_mysqldb import MySQL
import fitz  # PyMuPDF
import requests
import os
import google.generativeai as genai
import MySQLdb.cursors
import re
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24)

load_dotenv()  # Load environment variables from a .env file

# Configure Google API Key directly
genai.configure(api_key='AIzaSyAFt3EOfTkY5eZXF3k-9IDowvUTL6lBPJo')

app.config['MYSQL_HOST'] = os.getenv('DB_HOST', 'localhost')  # Set default value for local development
app.config['MYSQL_USER'] = os.getenv('DB_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD', '123456789')
app.config['MYSQL_DB'] = os.getenv('DB_NAME', 'users')

mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf_file = request.files['pdf_file']
        if pdf_file:
            pdf_text = process_pdf(pdf_file)
            session['pdf_text'] = pdf_text
            if 'loggedin' in session and session['loggedin']:
                return redirect(url_for('chat'))
            else:
                return redirect(url_for('login'))
    if 'loggedin' in session and session['loggedin']:
        return render_template('index.html')
    return render_template('login.html')


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'pdf_text' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        user_input = request.form['message']
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(session['pdf_text'] + "\n\n" + user_input)
        if 'history' not in session:
            session['history'] = []
        session['history'].append({'role': 'user', 'text': user_input})
        session['history'].append({'role': 'model', 'text': response.text})
    else:
        session['history'] = []

    history_display = '\n\n'.join(f"**{item['role']}**: {item['text']}" for item in session['history'])
    return render_template('chat.html', history=history_display)

def process_pdf(pdf_file):
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    pdf_text = ''
    for page in pdf_document:
        pdf_text += page.get_text()
    pdf_document.close()
    return pdf_text

def query_gemini_api(pdf_text, question):
    headers = {
        'Authorization': 'Bearer AIzaSyAFt3EOfTkY5eZXF3k-9IDowvUTL6lBPJo',
        'Content-Type': 'application/json'
    }
    data = {
        'documents': [pdf_text],
        'question': question
    }
    response = requests.post('https://api.gemini.com/query', headers=headers, json=data)
    return response.json().get('answers', ['No answer found'])[0]

@app.route('/login', methods=['GET', 'POST'])
def login():
    mesage = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s AND password = %s', (email, password,))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            mesage = 'Logged in successfully!'
            return render_template('index.html', mesage=mesage)
        else:
            mesage = 'Please enter correct email / password!'
    return render_template('login.html', mesage=mesage)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    mesage = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            mesage = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            mesage = 'Invalid email address!'
        elif not userName or not password or not email:
            mesage = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO user VALUES (NULL, %s, %s, %s)', (userName, email, password,))
            mysql.connection.commit()
            mesage = 'You have successfully registered!'
    elif request.method == 'POST':
        mesage = 'Please fill out the form!'
    return render_template('register.html', mesage=mesage)

if __name__ == '__main__':
    app.run(debug=True) 