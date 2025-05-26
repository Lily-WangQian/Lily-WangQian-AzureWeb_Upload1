from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load CSVs
bank_similarity_df = pd.read_csv('standards and banks detailed similarity score.csv')
bank_similarity_df.set_index('Standard', inplace=True)

bank_keywords_df = pd.read_csv('banks keywords.csv')
standard_keywords_df = pd.read_csv('standards keywords.csv')

# Extract names
bank_names = list(bank_similarity_df.columns)
standard_names = list(bank_similarity_df.index)

@app.route('/')
def index():
    return render_template('index.html', banks=bank_names, standards=standard_names, result=None)

@app.route('/calculate', methods=['POST'])
def calculate():
    bank = request.form['bank']
    standard = request.form['standard']

    try:
        score = round(bank_similarity_df.loc[standard, bank], 3)
    except KeyError:
        score = 'N/A'

    # Extract bank info
    bank_data = bank_keywords_df[bank_keywords_df['Bank'].str.strip() == bank]
    bank_info = {
        'report': bank_data.iloc[0]['Report'] if not bank_data.empty else 'N/A',
        'date': bank_data.iloc[0]['Publication Date'] if not bank_data.empty else 'N/A',
        'tfidf': bank_data.iloc[0]['TFIDF Keywords'] if not bank_data.empty else 'N/A',
        'contextual': bank_data.iloc[0]['Contextual Keywords'] if not bank_data.empty else 'N/A',
    }

    # Extract standard info
    standard_data = standard_keywords_df[standard_keywords_df['Standard'].str.strip() == standard]
    standard_info = {
        'report': standard_data.iloc[0]['Standard'] if not standard_data.empty else 'N/A',
        'date': standard_data.iloc[0]['Publication Date'] if not standard_data.empty else 'N/A',
        'tfidf': standard_data.iloc[0]['TFIDF Keywords'] if not standard_data.empty else 'N/A',
        'contextual': standard_data.iloc[0]['Contextual Keywords'] if not standard_data.empty else 'N/A',
    }

    return render_template('index.html', banks=bank_names, standards=standard_names, result={
        'bank': bank,
        'standard': standard,
        'score': score,
        'bank_info': bank_info,
        'standard_info': standard_info
    })

if __name__ == '__main__':
    app.run(debug=True)
