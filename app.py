import os
import re
import tempfile
import pdfplumber
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
from sklearn.feature_extraction.text import TfidfVectorizer

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './temp_uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure temp folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Azure Blob Storage
AZURE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
AZURE_CONTAINER_NAME = os.environ.get('AZURE_STORAGE_CONTAINER_NAME', 'uploads')

if AZURE_CONNECTION_STRING:
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)
else:
    blob_service_client = None
    container_client = None

# Stopwords
custom_stopwords = {'the', 'and', 'to', 'of', 'a', 'in', 'that', 'is', 'on', 'for', 'with', 'as', 'by', 'it', 'an'}

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\r\n]+', ' ', text)
    text = ' '.join(word for word in text.split() if word.lower() not in custom_stopwords)
    return text.strip()

def extract_text_from_pdf(path):
    with pdfplumber.open(path) as pdf:
        text = ' '.join(page.extract_text() for page in pdf.pages if page.extract_text())
    return clean_text(text)

def extract_tfidf_keywords(text, top_n=5):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=top_n)
    tfidf_matrix = vectorizer.fit_transform([text])
    return vectorizer.get_feature_names_out()

# Routes
@app.route('/')
def index():
    uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
    uploaded_files = [f for f in uploaded_files if allowed_file(f)]
    return render_template('index.html', uploaded_filenames=uploaded_files, keyword_results=None, error=None)

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('files')

    if len(files) < 2 or len(files) > 10:
        return render_template('index.html', uploaded_filenames=[], error="Upload between 2 and 10 PDF files.", keyword_results=None)

    uploaded_filenames = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            uploaded_filenames.append(filename)

    return redirect(url_for('index'))

@app.route('/remove', methods=['POST'])
def remove_file():
    filename = request.form.get('filename')
    if filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    return redirect(url_for('index'))

@app.route('/calculate', methods=['POST'])
def calculate_similarity():
    filenames = request.form.getlist('uploaded_files')

    if not filenames or len(filenames) < 2:
        return render_template('index.html', uploaded_filenames=[], keyword_results=None, error="At least 2 documents are required.")

    if container_client is None:
        return render_template('index.html', uploaded_filenames=[], keyword_results=None, error="Azure connection missing.")

    keyword_results = []

    for filename in filenames:
        local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Upload to Azure
        blob_client = container_client.get_blob_client(filename)
        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        # Clean and extract
        cleaned_text = extract_text_from_pdf(local_path)
        tfidf_keywords = extract_tfidf_keywords(cleaned_text)

        keyword_results.append({
            'filename': filename,
            'tfidf_keywords': tfidf_keywords
        })

        # Remove temp file
        os.remove(local_path)

    return render_template('index.html', uploaded_filenames=[], keyword_results=keyword_results, error=None)

if __name__ == '__main__':
    app.run(debug=True)
