from flask import Flask, request, render_template, redirect, url_for, session
import fitz  # PyMuPDF
import requests
import os
import google.generativeai as genai
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
import bcrypt

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///databse.db'
db = SQLAlchemy(app)
app.secret_key = 'decret_key'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self,email,password,name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.getsalt()).decode('utf-8')

    def check_password(self,password):
        return bcrypt.checkpw(password.encode('utf-8'),self.password.encode('utf-8'))  

with app.app_context():
    db.create_all()          

load_dotenv()  # Load environment variables from a .env file

# Configure Google API Key directly
genai.configure(api_key='AIzaSyAFt3EOfTkY5eZXF3k-9IDowvUTL6lBPJo')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf_file = request.files['pdf_file']
        if pdf_file:
            pdf_text = process_pdf(pdf_file)
            session['pdf_text'] = pdf_text
            return redirect(url_for('chat'))
    return render_template('upload.html')

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

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # handle request
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        new_user = User(name=name,email=email,password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

          
    return render_template('register.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
          email = request.form['email']
          password = request.form['password']

          user = User.query.filter_by(email=email).first()

          if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/dashboard')
        else:
            return render_template('login.html',error='Invalid user')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if session['name']
    user = User.query.filter_by(email=session['email']).first()
    return render_template('dashboard.html',user=user)

return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('email',None)
    return redirect('/login')

if __name__=='__main__':
    app.run(debug=True)