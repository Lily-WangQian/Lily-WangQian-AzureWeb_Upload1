import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Initialize Azure Blob Storage
AZURE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
AZURE_CONTAINER_NAME = os.environ.get('AZURE_STORAGE_CONTAINER_NAME', 'uploads')

# Only initialize blob_service_client if connection string exists
if AZURE_CONNECTION_STRING:
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)
else:
    blob_service_client = None
    container_client = None

# Helper function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Upload route
@app.route('/upload', methods=['POST'])
def upload_files():
    if container_client is None:
        return render_template('index.html', error="Storage connection not configured.")

    files = request.files.getlist('files')
    if not files:
        return render_template('index.html', error="No files selected.")
    
    uploaded_files = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(local_path)

            # Upload to Azure Blob Storage
            blob_client = container_client.get_blob_client(filename)
            with open(local_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)

            uploaded_files.append(filename)

    return render_template('index.html', uploaded_files=uploaded_files)

if __name__ == '__main__':
    app.run(debug=True)
