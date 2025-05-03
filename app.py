import os
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

# Load similarity matrix
similarity_file = 'banks and banks detailed similarity score.csv'
similarity_df = pd.read_csv(similarity_file, index_col='Banks')

if 'Unnamed: 0' in similarity_df.columns:
    similarity_df = similarity_df.drop(columns=['Unnamed: 0'])

banks = similarity_df.columns.tolist()

# Load ESG keyword data
esg_file = 'banks keywords.csv'
esg_df = pd.read_csv(esg_file)

@app.route('/')
def index():
    return render_template('index.html', banks=banks, similarity_result=None, esg_data=None, error=None)

@app.route('/calculate', methods=['POST'])
def calculate_similarity():
    bank1 = request.form.get('bank1')
    bank2 = request.form.get('bank2')

    if not bank1 or not bank2:
        return render_template('index.html', banks=banks, similarity_result=None, esg_data=None, error="Please select two banks.")

    try:
        score = similarity_df.loc[bank1, bank2]
    except KeyError:
        score = 'N/A'

    # Get ESG details
    esg_bank1 = esg_df[esg_df['Bank'].str.lower() == bank1.lower()]
    esg_bank2 = esg_df[esg_df['Bank'].str.lower() == bank2.lower()]

    return render_template('index.html',
                           banks=banks,
                           similarity_result={'bank1': bank1, 'bank2': bank2, 'score': score},
                           esg_data={
                               'bank1': esg_bank1[['Report', 'Publication Date', 'TFIDF Key', 'Contextual Combined Keywords']].to_dict(orient='records'),
                               'bank2': esg_bank2[['Report', 'Publication Date', 'TFIDF Key', 'Contextual Combined Keywords']].to_dict(orient='records')
                           },
                           error=None)

if __name__ == '__main__':
    app.run(debug=True)
