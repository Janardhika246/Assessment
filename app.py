from flask import Flask, request, render_template, redirect, url_for, session
import fitz  # PyMuPDF
import requests
import os
import google.generativeai as genai
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24)

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
