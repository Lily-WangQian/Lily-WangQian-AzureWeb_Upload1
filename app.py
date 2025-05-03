from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load data
similarity_df = pd.read_csv('banks and banks detailed similarity score.csv', index_col=0)
keywords_df = pd.read_csv('banks keywords.csv')

# Clean header if needed
banks = [col for col in similarity_df.columns if col != 'Banks']

@app.route('/')
def index():
    return render_template('index.html', banks=banks)

@app.route('/calculate', methods=['POST'])
def calculate():
    bank1 = request.form['bank1']
    bank2 = request.form['bank2']

    try:
        score = similarity_df.loc[bank1, bank2]
    except KeyError:
        score = 'N/A'

    bank1_data_row = keywords_df[keywords_df['Bank'] == bank1].iloc[0]
    bank2_data_row = keywords_df[keywords_df['Bank'] == bank2].iloc[0]

    bank1_data = {
        'Report': bank1_data_row['Report'],
        'Publication Date': bank1_data_row['Publication Date'],
        'TFIDF Keywords': bank1_data_row['TFIDF Keywords'],
        'Contextual Keywords': bank1_data_row['Contextual Keywords']
    }

    bank2_data = {
        'Report': bank2_data_row['Report'],
        'Publication Date': bank2_data_row['Publication Date'],
        'TFIDF Keywords': bank2_data_row['TFIDF Keywords'],
        'Contextual Keywords': bank2_data_row['Contextual Keywords']
    }

    return render_template('index.html', banks=banks, bank1=bank1, bank2=bank2, score=score,
                           bank1_data=bank1_data, bank2_data=bank2_data)

if __name__ == '__main__':
    app.run(debug=True)
