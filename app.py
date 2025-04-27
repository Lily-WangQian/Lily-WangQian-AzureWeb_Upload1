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
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Load Azure Blob Storage
AZURE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
AZURE_CONTAINER_NAME = os.environ.get('AZURE_STORAGE_CONTAINER_NAME', 'uploads')

if AZURE_CONNECTION_STRING:
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)
else:
    blob_service_client = None
    container_client = None

# Custom stopwords
custom_stopwords = {'the', 'and', 'to', 'of', 'a', 'in', 'that', 'is', 'on', 'for', 'with', 'as', 'by', 'it', 'an'}

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_text_from_pdf(pdf_bytes):
    """Extract and clean text from a PDF file given bytes."""
    with pdfplumber.open(pdf_bytes) as pdf:
        text = ' '.join(page.extract_text() for page in pdf.pages if page.extract_text())
    return clean_text(text)

def clean_text(text):
    """Clean and preprocess extracted text."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\r\n]+', ' ', text)
    text = ' '.join(word for word in text.split() if word.lower() not in custom_stopwords)
    return text.strip()

def extract_tfidf_keywords(text, top_n=5):
    """Extract top TF-IDF keywords."""
    vectorizer = TfidfVectorizer(stop_words='english', max_features=top_n)
    tfidf_matrix = vectorizer.fit_transform([text])
    return vectorizer.get_feature_names_out()

# Routes
@app.route('/')
def index():
    return render_template('index.html', uploaded_files=None, keyword_results=None, error=None)

@app.route('/upload', methods=['POST'])
def upload_files():
    if container_client is None:
        return render_template('index.html', error="Azure Storage connection not configured.")

    files = request.files.getlist('files')
    if not files:
        return render_template('index.html', error="No files selected.")

    uploaded_files = []
    keyword_results = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Upload file to Azure Blob
            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(file.read(), overwrite=True)
            uploaded_files.append(filename)

            # Download the file back temporarily to process
            temp = tempfile.NamedTemporaryFile(delete=False)
            blob_data = blob_client.download_blob()
            temp.write(blob_data.readall())
            temp.close()

            # Extract text and keywords
            with pdfplumber.open(temp.name) as pdf:
                full_text = ' '.join(page.extract_text() for page in pdf.pages if page.extract_text())
            cleaned_text = clean_text(full_text)
            tfidf_keywords = extract_tfidf_keywords(cleaned_text)

            keyword_results.append({
                'filename': filename,
                'tfidf_keywords': tfidf_keywords
            })

            # Delete temporary file
            os.remove(temp.name)

    return render_template('index.html', uploaded_files=uploaded_files, keyword_results=keyword_results, error=None)

if __name__ == '__main__':
    app.run(debug=True)
