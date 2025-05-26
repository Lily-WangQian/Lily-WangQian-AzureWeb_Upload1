from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load similarity scores and remove unnamed index column if present
similarity_df = pd.read_csv('standards and banks detailed similarity score.csv')
if 'Unnamed: 0' in similarity_df.columns:
    similarity_df = similarity_df.drop(columns=['Unnamed: 0'])
similarity_df.set_index('Standard', inplace=True)

# Load keyword data and remove unnamed index columns if present
bank_keywords_df = pd.read_csv('banks keywords.csv')
standard_keywords_df = pd.read_csv('standards keywords.csv')

# Clean unnamed columns in keyword files too
for df in [bank_keywords_df, standard_keywords_df]:
    df.drop(columns=[col for col in df.columns if 'Unnamed' in col], inplace=True)

# Get clean bank and standard names
bank_names = [col for col in similarity_df.columns if not col.startswith('Unnamed')]
standard_names = list(similarity_df.index)

@app.route('/')
def index():
    return render_template('index.html', banks=bank_names, standards=standard_names, result=None)

@app.route('/calculate', methods=['POST'])
def calculate():
    bank = request.form['bank']
    standard = request.form['standard']

    try:
        score = round(similarity_df.loc[standard, bank], 3)
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
