from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load similarity scores
similarity_df = pd.read_csv('standards and banks detailed similarity score.csv')

# Drop unnamed columns
similarity_df = similarity_df.loc[:, ~similarity_df.columns.str.contains('^Unnamed')]

# Set index for standards
similarity_df.set_index('Standard', inplace=True)

# Load keyword details
bank_keywords_df = pd.read_csv('banks keywords.csv')
standard_keywords_df = pd.read_csv('standards keywords.csv')

# Clean bank names
bank_names = [col for col in similarity_df.columns if col.lower() != 'unnamed: 0']
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
        print(f"Error calculating similarity: {e}")
        score = 'N/A'

    # Extract bank info safely
    bank_row = bank_keywords_df[bank_keywords_df['Bank'].str.strip() == bank]
    bank_info = {
        'report': bank_row.iloc[0]['Report'] if not bank_row.empty else 'N/A',
        'date': bank_row.iloc[0]['Publication Date'] if not bank_row.empty else 'N/A',
        'tfidf': bank_row.iloc[0].get('TFIDF Keywords', 'N/A') if not bank_row.empty else 'N/A',
        'contextual': bank_row.iloc[0].get('Contextual Keywords', 'N/A') if not bank_row.empty else 'N/A',
    }

    # Extract standard info safely
    std_row = standard_keywords_df[standard_keywords_df['Standard'].str.strip() == standard]
    standard_info = {
        'report': std_row.iloc[0]['Standard'] if not std_row.empty else 'N/A',
        'date': std_row.iloc[0]['Publication Date'] if not std_row.empty else 'N/A',
        'tfidf': std_row.iloc[0].get('TFIDF Keywords', 'N/A') if not std_row.empty else 'N/A',
        'contextual': std_row.iloc[0].get('Contextual Keywords', 'N/A') if not std_row.empty else 'N/A',
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
