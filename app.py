from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load and clean data
similarity_df = pd.read_csv('standards and banks detailed similarity score.csv')
similarity_df = similarity_df.loc[:, ~similarity_df.columns.str.contains('^Unnamed', case=False)]
similarity_df.columns = similarity_df.columns.str.strip()
similarity_df.set_index('Standard', inplace=True)

bank_keywords_df = pd.read_csv('banks keywords.csv')
bank_keywords_df.columns = bank_keywords_df.columns.str.strip()

standard_keywords_df = pd.read_csv('standards keywords.csv')
standard_keywords_df.columns = standard_keywords_df.columns.str.strip()

# Extract bank and standard names
bank_names = similarity_df.columns.tolist()
standard_names = similarity_df.index.tolist()

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

    # Bank info
    bank_row = bank_keywords_df[bank_keywords_df['Bank'].str.strip() == bank]
    bank_info = {
        'report': bank_row.iloc[0]['Report'] if not bank_row.empty else 'N/A',
        'date': bank_row.iloc[0]['Publication Date'] if not bank_row.empty else 'N/A',
        'tfidf': bank_row.iloc[0]['TFIDF Keywords'] if not bank_row.empty else 'N/A',
        'contextual': bank_row.iloc[0]['Contextual Keywords'] if not bank_row.empty else 'N/A',
    }

    # Standard info
    std_row = standard_keywords_df[standard_keywords_df['Standard'].str.strip() == standard]
    standard_info = {
        'report': std_row.iloc[0]['Standard'] if not std_row.empty else 'N/A',
        'date': std_row.iloc[0]['Publication Date'] if not std_row.empty else 'N/A',
        'tfidf': std_row.iloc[0]['TFIDF Keywords'] if not std_row.empty else 'N/A',
        'contextual': std_row.iloc[0]['Contextual Keywords'] if not std_row.empty else 'N/A',
    }

    return render_template(
        'index.html',
        banks=bank_names,
        standards=standard_names,
        result={
            'bank': bank,
            'standard': standard,
            'score': score,
            'bank_info': bank_info,
            'standard_info': standard_info
        }
    )

if __name__ == '__main__':
    app.run(debug=True)
