from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load similarity matrix (bank vs standards)
similarity_df = pd.read_csv('standards and banks detailed similarity score.csv', index_col=0)

# Load ESG details
banks_df = pd.read_csv('banks keywords.csv')
standards_df = pd.read_csv('standards keywords.csv')

# Clean bank/standard names from CSV
banks = list(similarity_df.columns)
standards = list(similarity_df.index)

@app.route('/')
def index():
    return render_template('index.html', banks=banks, standards=standards, result=None)

@app.route('/calculate', methods=['POST'])
def calculate():
    selected_bank = request.form['bank']
    selected_standard = request.form['standard']

    # Try to retrieve similarity score
    try:
        score = similarity_df.loc[selected_standard, selected_bank]
        score = round(score, 3)
    except KeyError:
        score = 'N/A'

    # Get bank ESG info
    bank_data = banks_df[banks_df['Bank'].str.strip() == selected_bank].iloc[0]
    bank_info = {
        'report': bank_data['Report'],
        'date': bank_data['Publication Date'],
        'tfidf': bank_data['TFIDF Keywords'],
        'contextual': bank_data['Contextual Keywords']
    }

    # Get standard ESG info
    std_data = standards_df[standards_df['Standard'].str.strip() == selected_standard].iloc[0]
    standard_info = {
        'report': std_data['Report'],
        'date': std_data['Publication Date'],
        'tfidf': std_data['TFIDF Keywords'],
        'contextual': std_data['Contextual Keywords']
    }

    return render_template('index.html',
                           banks=banks,
                           standards=standards,
                           result={
                               'bank': selected_bank,
                               'standard': selected_standard,
                               'score': score,
                               'bank_info': bank_info,
                               'standard_info': standard_info
                           })

if __name__ == '__main__':
    app.run(debug=True)
