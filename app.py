from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load similarity scores (set 'Banks' column as index)
similarity_df = pd.read_csv('banks and banks detailed similarity score.csv')
similarity_df.set_index('Banks', inplace=True)

# Load keyword details
keywords_df = pd.read_csv('banks keywords.csv')

# Get clean list of bank names (from similarity_df index)
bank_names = list(similarity_df.index)

@app.route('/')
def index():
    return render_template('index.html', banks=bank_names, result=None)

@app.route('/calculate', methods=['POST'])
def calculate():
    bank1 = request.form['bank1']
    bank2 = request.form['bank2']

    # Get similarity score safely
    try:
        score = similarity_df.loc[bank1, bank2]
        score = round(score, 3)  # round to 3 decimals
    except KeyError:
        score = 'N/A'

    # Get bank 1 details
    bank1_data = keywords_df[keywords_df['Bank'].str.strip() == bank1]
    if not bank1_data.empty:
        bank1_info = {
            'report': bank1_data.iloc[0]['Report'],
            'date': bank1_data.iloc[0]['Publication Date'],
            'tfidf': bank1_data.iloc[0]['TFIDF Keywords'],
            'contextual': bank1_data.iloc[0]['Contextual Keywords']
        }
    else:
        bank1_info = {'report': 'N/A', 'date': 'N/A', 'tfidf': 'N/A', 'contextual': 'N/A'}

    # Get bank 2 details
    bank2_data = keywords_df[keywords_df['Bank'].str.strip() == bank2]
    if not bank2_data.empty:
        bank2_info = {
            'report': bank2_data.iloc[0]['Report'],
            'date': bank2_data.iloc[0]['Publication Date'],
            'tfidf': bank2_data.iloc[0]['TFIDF Keywords'],
            'contextual': bank2_data.iloc[0]['Contextual Keywords']
        }
    else:
        bank2_info = {'report': 'N/A', 'date': 'N/A', 'tfidf': 'N/A', 'contextual': 'N/A'}

    return render_template('index.html', banks=bank_names, result={
        'bank1': bank1,
        'bank2': bank2,
        'score': score,
        'bank1_info': bank1_info,
        'bank2_info': bank2_info
    })

if __name__ == '__main__':
    app.run(debug=True)
