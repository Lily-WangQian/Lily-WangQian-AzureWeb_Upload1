import os
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

# Load CSV and clean up 'Unnamed: 0' if present
CSV_FILE = 'banks and banks detailed similarity score.csv'
similarity_df = pd.read_csv(CSV_FILE, index_col='Banks')

# Drop unnecessary columns if they exist
if 'Unnamed: 0' in similarity_df.columns:
    similarity_df = similarity_df.drop(columns=['Unnamed: 0'])

# Get list of bank names from the cleaned DataFrame
banks = similarity_df.columns.tolist()

@app.route('/')
def index():
    return render_template('index.html', banks=banks, similarity_result=None, error=None)

@app.route('/calculate', methods=['POST'])
def calculate_similarity():
    bank1 = request.form.get('bank1')
    bank2 = request.form.get('bank2')

    if not bank1 or not bank2:
        return render_template('index.html', banks=banks, similarity_result=None, error="Please select two banks.")

    try:
        score = similarity_df.loc[bank1, bank2]
    except KeyError:
        score = 'N/A'

    return render_template('index.html',
                           banks=banks,
                           similarity_result={'bank1': bank1, 'bank2': bank2, 'score': score},
                           error=None)

if __name__ == '__main__':
    app.run(debug=True)
