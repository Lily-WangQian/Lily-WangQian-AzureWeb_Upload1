from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load similarity and keyword data
similarity_df = pd.read_csv('banks and banks detailed similarity score.csv', index_col=0)
keywords_df = pd.read_csv('banks keywords.csv')

# Clean bank names
bank_names = [name.strip() for name in similarity_df.columns]

@app.route('/')
def index():
    return render_template('index.html', banks=bank_names, result=None)

@app.route('/calculate', methods=['POST'])
def calculate():
    bank1 = request.form['bank1']
    bank2 = request.form['bank2']

    # Get similarity score
    try:
        score = similarity_df.loc[bank1, bank2]
    except KeyError:
        score = 'N/A'

    # Get keywords for both banks
    bank1_data = keywords_df[keywords_df['Bank'].str.strip() == bank1].iloc[0]
    bank2_data = keywords_df[keywords_df['Bank'].str.strip() == bank2].iloc[0]

    bank1_info = {
        'report': bank1_data['Report'],
        'date': bank1_data['Publication Date'],
        'tfidf': bank1_data['TFIDF Keywords'],
        'contextual': bank1_data['Contextual Keywords']
    }

    bank2_info = {
        'report': bank2_data['Report'],
        'date': bank2_data['Publication Date'],
        'tfidf': bank2_data['TFIDF Keywords'],
        'contextual': bank2_data['Contextual Keywords']
    }

    return render_template('index.html', banks=bank_names, result={
        'bank1': bank1,
        'bank2': bank2,
        'score': score,
        'bank1_info': bank1_info,
        'bank2_info': bank2_info
    })

if __name__ == '__main__':
    app.run(debug=True)
