from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import fitz  # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv
import re
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

load_dotenv()  # Load environment variables from a .env file

# Configure Google API Key directly
genai.configure(api_key='AIzaSyAFt3EOfTkY5eZXF3k-9IDowvUTL6lBPJo')

# SQLite configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf_file = request.files.get('pdf_file')
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

def separate_points(text):
    # This function can be customized based on your specific needs
    # For now, we'll use newlines as separators
    return text.split('\n')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'pdf_text' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        user_input = request.form['message']
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(session['pdf_text'] + "\n\n" + user_input)

        # Process the response to separate points
        separated_response = separate_points(response.text)

        # Initialize chat history if not present
        if 'chat_history' not in session:
            session['chat_history'] = []

        # Append new messages to chat history with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        session['chat_history'].append({'role': 'user', 'text': user_input, 'timestamp': timestamp})
        session['chat_history'].append({'role': 'model', 'text': separated_response, 'timestamp': timestamp})

    # Display entire chat history for the current PDF
    return render_template('chat.html', history=session.get('chat_history', []))


def process_pdf(pdf_file):
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    pdf_text = ''
    for page in pdf_document:
        # Extract text from the page
        page_text = page.get_text("text")
        
        # Split the text into paragraphs based on blank lines
        paragraphs = page_text.split('\n\n')
        
        # Join paragraphs with a break (or any other separator)
        joined_paragraphs = '\n\n'.join(paragraphs)
        
        pdf_text += joined_paragraphs
    
    pdf_document.close()
    return pdf_text

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['loggedin'] = True
            session['userid'] = user.id
            session['name'] = user.name
            session['email'] = user.email
            message = 'Logged in successfully!'
            return redirect(url_for('index'))
        else:
            message = 'Please enter correct email / password!'
    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))


   

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not userName or not password or not email:
            message = 'Please fill out the form!'
        else:
            new_user = User(name=userName, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            message = 'You have successfully registered!'
    elif request.method == 'POST':
        message = 'Please fill out the form!'
    return render_template('register.html', message=message)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
