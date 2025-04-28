import os
import re
import tempfile
import pdfplumber
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
from sklearn.feature_extraction.text import TfidfVectorizer

# Initialize Flask app
app = Flask(__name__)
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

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

def extract_text_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ' '.join(page.extract_text() for page in pdf.pages if page.extract_text())
    return clean_text(text)

def extract_tfidf_keywords(text, top_n=5):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=top_n)
    tfidf_matrix = vectorizer.fit_transform([text])
    return vectorizer.get_feature_names_out()

# Routes
@app.route('/')
def index():
    blobs = []
    if container_client:
        blobs = [blob.name for blob in container_client.list_blobs()]
    return render_template('index.html', uploaded_filenames=blobs, keyword_results=None, error=None)

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('files')

    if not (2 <= len(files) <= 10):
        return render_template('index.html', uploaded_filenames=[], keyword_results=None, error="Please upload between 2 and 10 PDF files.")

    if container_client is None:
        return render_template('index.html', uploaded_filenames=[], keyword_results=None, error="Azure Storage not configured.")

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(file.read(), overwrite=True)

    return redirect(url_for('index'))

@app.route('/calculate', methods=['POST'])
def calculate_similarity():
    filenames = request.form.getlist('uploaded_files')

    if not filenames or len(filenames) < 2:
        return render_template('index.html', uploaded_filenames=[], keyword_results=None, error="Please select at least 2 documents.")

    if container_client is None:
        return render_template('index.html', uploaded_filenames=[], keyword_results=None, error="Azure Storage not configured.")

    keyword_results = []

    for filename in filenames:
        blob_client = container_client.get_blob_client(filename)
        temp_file = tempfile.NamedTemporaryFile(delete=False)

        # Download blob to temp file
        download_stream = blob_client.download_blob()
        temp_file.write(download_stream.readall())
        temp_file.close()

        # Clean and extract
        cleaned_text = extract_text_from_pdf(temp_file.name)
        tfidf_keywords = extract_tfidf_keywords(cleaned_text)

        keyword_results.append({
            'filename': filename,
            'tfidf_keywords': tfidf_keywords
        })

        os.remove(temp_file.name)

    blobs = [blob.name for blob in container_client.list_blobs()]
    return render_template('index.html', uploaded_filenames=blobs, keyword_results=keyword_results, error=None)

if __name__ == '__main__':
    app.run(debug=True)
