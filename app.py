from flask import Flask, request, render_template, redirect, url_for, session
import fitz  # PyMuPDF
import requests
import os
import google.generativeai as genai
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load environment variables from a .env file
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Handle the uploaded PDF file
        pdf_file = request.files['pdf_file']
        if pdf_file:
            pdf_text = process_pdf(pdf_file)
            session['pdf_text'] = pdf_text  # Store extracted text in session for chat reference
            return redirect(url_for('chat'))
    return render_template('upload.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'pdf_text' not in session:
        return redirect(url_for('index'))  # Redirect to upload if no PDF text is stored

    if request.method == 'POST':
        user_input = request.form['message']
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat_session = model.start_chat(history=[])  # Start a new chat session
        response = chat_session.send_message(session['pdf_text'] + "\n\n" + user_input)
        
        # Initialize history if not present
        if 'history' not in session:
            session['history'] = []

        session['history'].append({'role': 'user', 'text': user_input})
        session['history'].append({'role': 'model', 'text': response.text})
    else:
        session['history'] = []

    history_display = '\n\n'.join(f"**{item['role']}**: {item['text']}" for item in session['history'])
    return render_template('chat.html', history=history_display)

def process_pdf(file):
    # Using PyMuPDF to extract text from the PDF
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
    pdf_text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        pdf_text += page.get_text()
    pdf_document.close()
    return pdf_text

def query_gemini_api(pdf_text, question):
    headers = {
        'Authorization': f'Bearer {GOOGLE_API_KEY}',  # Your Gemini API key
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
