from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load similarity scores
similarity_df = pd.read_csv('standards and banks detailed similarity score.csv')

# Remove the 'Unnamed: 0' column if present
if 'Unnamed: 0' in similarity_df.columns:
    similarity_df.drop(columns=['Unnamed: 0'], inplace=True)

# Set standard column as index
similarity_df.set_index('Standard', inplace=True)

# Load keywords data
bank_keywords_df = pd.read_csv('banks keywords.csv')
standard_keywords_df = pd.read_csv('standards keywords.csv')

# Get clean list of bank names (excluding anything like 'Unnamed: 0')
bank_names = [col for col in similarity_df.columns if not col.lower().startswith('unnamed')]
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

    bank_data = bank_keywords_df[bank_keywords_df['Bank'].str.strip() == bank]
    bank_info = {
        'report': bank_data.iloc[0]['Report'] if not bank_data.empty else 'N/A',
        'date': bank_data.iloc[0]['Publication Date'] if not bank_data.empty else 'N/A',
        'tfidf': bank_data.iloc[0]['TFIDF Keywords'] if not bank_data.empty else 'N/A',
        'contextual': bank_data.iloc[0]['Contextual Keywords'] if not bank_data.empty else 'N/A',
    }

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
