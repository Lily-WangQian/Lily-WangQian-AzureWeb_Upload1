from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load and clean the similarity score CSV
similarity_df = pd.read_csv('standards and banks detailed similarity score.csv')
similarity_df = similarity_df.loc[:, ~similarity_df.columns.str.contains('^Unnamed', case=False)]
similarity_df.columns = similarity_df.columns.str.strip()
similarity_df.set_index('Standard', inplace=True)

# Extract bank and standard names
bank_names = similarity_df.columns.tolist()
standard_names = similarity_df.index.tolist()

@app.route('/')
def index():
    return render_template('index.html', banks=bank_names, standards=standard_names, score=None)

@app.route('/calculate', methods=['POST'])
def calculate():
    bank = request.form['bank']
    standard = request.form['standard']

    try:
        score = round(float(similarity_df.loc[standard, bank]), 3)
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        score = 'N/A'

    return render_template('index.html', banks=bank_names, standards=standard_names, score=score, bank=bank, standard=standard)

if __name__ == '__main__':
    app.run(debug=True)
