from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load and clean similarity score CSV
similarity_df = pd.read_csv('standards and banks detailed similarity score.csv')
similarity_df = similarity_df.loc[:, ~similarity_df.columns.str.contains('^Unnamed', case=False)]
similarity_df.columns = similarity_df.columns.str.strip()
similarity_df.set_index('Standard', inplace=True)

# Load ESG keyword data
bank_keywords_df = pd.read_csv('banks keywords.csv')
standard_keywords_df = pd.read_csv('standards keywords.csv')

# Clean column names
bank_keywords_df.columns = bank_keywords_df.columns.str.strip()
standard_keywords_df.columns = standard_keywords_df.columns.str.strip()

# Get valid names
bank_names = similarity_df.columns.tolist()
standard_names = similarity_df.index.tolist()

@app.route('/')
def index():
    return render_template('index.html',
                           banks=bank_names,
                           standards=standard_names,
                           score=None,
                           bank=None,
                           standard=None,
                           bank_table=None,
                           standard_table=None)

@app.route('/calculate', methods=['POST'])
def calculate():
    bank = request.form['bank']
    standard = request.form['standard']

    try:
        score = round(float(similarity_df.loc[standard, bank]), 3)
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        score = 'N/A'

    # Prepare bank ESG report
    bank_data = bank_keywords_df[bank_keywords_df['Bank'].str.lower().str.strip() == bank.lower()]
    if not bank_data.empty:
        bank_data = bank_data[['Report', 'Publication Date', 'TFIDF Keywords', 'Contextual Keywords']]
        bank_table = bank_data.to_html(classes='table table-bordered', index=False)
    else:
        bank_table = "<p>No data found for selected bank.</p>"

    # Prepare standard ESG report
    standard_data = standard_keywords_df[standard_keywords_df['Standard'].str.lower().str.strip() == standard.lower()]
    if not standard_data.empty:
        standard_data = standard_data[['Report', 'Publication Date', 'TFIDF Keywords', 'Contextual Keywords']]
        standard_table = standard_data.to_html(classes='table table-bordered', index=False)
    else:
        standard_table = "<p>No data found for selected standard.</p>"

    return render_template('index.html',
                           banks=bank_names,
                           standards=standard_names,
                           score=score,
                           bank=bank,
                           standard=standard,
                           bank_table=bank_table,
                           standard_table=standard_table)

if __name__ == '__main__':
    app.run(debug=True)
