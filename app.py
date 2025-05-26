from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load similarity scores between standards and banks
similarity_df = pd.read_csv('standards and banks detailed similarity score.csv')
similarity_df.set_index('Standards', inplace=True)

# Load keyword details
banks_keywords_df = pd.read_csv('banks keywords.csv')
standards_keywords_df = pd.read_csv('standards keywords.csv')

# Extract unique names
bank_names = sorted(banks_keywords_df['Bank'].unique())
standard_names = sorted(similarity_df.index)

@app.route('/')
def index():
    return render_template('index.html', banks=bank_names, standards=standard_names, result=None)

@app.route('/calculate', methods=['POST'])
def calculate():
    bank = request.form['bank']
    standard = request.form['standard']

    # Get similarity score
    try:
        score = similarity_df.loc[standard, bank]
        score = round(score, 3)
    except KeyError:
        score = 'N/A'

    # Get bank info
    bank_data = banks_keywords_df[banks_keywords_df['Bank'].str.strip() == bank]
    if not bank_data.empty:
        bank_info = {
            'report': bank_data.iloc[0]['Report'],
            'date': bank_data.iloc[0]['Publication Date'],
            'tfidf': ', '.join(bank_data.iloc[0]['TFIDF Keywords'].split(', ')[:5]),
            'contextual': ', '.join(bank_data.iloc[0]['Contextual Keywords'].split(', ')[:5])
        }
    else:
        bank_info = {'report': 'N/A', 'date': 'N/A', 'tfidf': 'N/A', 'contextual': 'N/A'}

    # Get standard info
    standard_data = standards_keywords_df[standards_keywords_df['Standard'].str.strip() == standard]
    if not standard_data.empty:
        standard_info = {
            'report': standard_data.iloc[0]['Report'],
            'date': standard_data.iloc[0]['Publication Date'],
            'tfidf': ', '.join(standard_data.iloc[0]['TFIDF Keywords'].split(', ')[:5]),
            'contextual': ', '.join(standard_data.iloc[0]['Contextual Keywords'].split(', ')[:5])
        }
    else:
        standard_info = {'report': 'N/A', 'date': 'N/A', 'tfidf': 'N/A', 'contextual': 'N/A'}

    return render_template('index.html', banks=bank_names, standards=standard_names, result={
        'bank': bank,
        'standard': standard,
        'score': score,
        'bank_info': bank_info,
        'standard_info': standard_info
    })

if __name__ == '__main__':
    app.run(debug=True)
