from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load and clean similarity scores
similarity_df = pd.read_csv('standards and banks detailed similarity score.csv')
similarity_df = similarity_df.loc[:, ~similarity_df.columns.str.contains('^Unnamed')]
similarity_df.columns = similarity_df.columns.str.strip()
similarity_df.set_index('Standard', inplace=True)

# Load and clean keyword files
bank_keywords_df = pd.read_csv('banks keywords.csv')
standard_keywords_df = pd.read_csv('standards keywords.csv')

# Clean headers
bank_keywords_df.columns = bank_keywords_df.columns.str.strip()
standard_keywords_df.columns = standard_keywords_df.columns.str.strip()

# Clean names
bank_names = [col.strip() for col in similarity_df.columns]
standard_names = list(similarity_df.index)

@app.route('/')
def index():
    return render_template('index.html', banks=bank_names, standards=standard_names, result=None)

@app.route('/calculate', methods=['POST'])
def calculate():
    bank = request.form['bank']
    standard = request.form['standard']

    try:
        score = round(float(similarity_df.loc[standard, bank]), 3)
    except Exception as e:
        print(f"Similarity error: {e}")
        score = 'N/A'

    # Get bank info
    bank_row = bank_keywords_df[bank_keywords_df['Bank'].str.strip() == bank]
    if not bank_row.empty:
        row = bank_row.iloc[0]
        bank_info = {
            'report': row.get('Report', 'N/A'),
            'date': row.get('Publication Date', 'N/A'),
            'tfidf': row.get('TFIDF Keywords', 'N/A'),
            'contextual': row.get('Contextual Keywords', 'N/A'),
        }
    else:
        bank_info = {'report': 'N/A', 'date': 'N/A', 'tfidf': 'N/A', 'contextual': 'N/A'}

    # Get standard info
    std_row = standard_keywords_df[standard_keywords_df['Standard'].str.strip() == standard]
    if not std_row.empty:
        row = std_row.iloc[0]
        standard_info = {
            'report': row.get('Standard', 'N/A'),
            'date': row.get('Publication Date', 'N/A'),
            'tfidf': row.get('TFIDF Keywords', 'N/A'),
            'contextual': row.get('Contextual Keywords', 'N/A'),
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
