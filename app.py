import os
import re
import string
import pdfplumber
import pandas as pd
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ALLOWED_EXTENSIONS"] = {"pdf"}
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ---------- Data sources ----------
# Use your existing standards CSV to populate the dropdown
# (column may be 'Standards' or 'Standard' depending on your file)
standards_df = pd.read_csv("standards keywords.csv")
col = "Standards" if "Standards" in standards_df.columns else "Standard"
standards = sorted(standards_df[col].dropna().astype(str).str.strip().unique().tolist())

# ---------- Models ----------
sbert = SentenceTransformer("all-MiniLM-L6-v2")  # light & fast

# ---------- Helpers ----------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

_punct_table = str.maketrans("", "", string.punctuation)
_custom_stop = {
    "the","and","to","of","a","in","that","is","on","for","with","as","by","it","an",
    "are","be","this","from","at","or","we","our","their","its","these","those"
}

def clean_text(text: str) -> str:
    # basic cleaning similar to your notebook approach:
    # lowercase, remove punctuation/numbers, collapse spaces, drop common stopwords
    text = text.lower()
    text = text.translate(_punct_table)
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    words = [w for w in text.split() if w not in _custom_stop and len(w) > 2]
    return " ".join(words)

def read_pdf_text(path: str) -> str:
    chunks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t:
                chunks.append(t)
    return "\n".join(chunks)

def tfidf_keywords(doc_text: str, top_n: int = 15, ngram_range=(1, 2)) -> list[str]:
    # Build a small vocab from the single doc (works fine for keyword surfacing)
    vec = TfidfVectorizer(stop_words="english", ngram_range=ngram_range, max_features=2000)
    X = vec.fit_transform([doc_text])
    # get feature scores
    scores = X.toarray().ravel()
    feats = vec.get_feature_names_out()
    ranked = sorted(zip(feats, scores), key=lambda x: x[1], reverse=True)
    return [w for w, _ in ranked[:top_n]]

def contextual_keywords(doc_text: str, top_n: int = 15, candidate_pool: int = 80) -> list[str]:
    """
    Rank candidate terms by cosine similarity to the full-document embedding.
    Candidates come from TF-IDF top terms (1–2 grams). Returns keywords (not sentences).
    """
    candidates = tfidf_keywords(doc_text, top_n=candidate_pool, ngram_range=(1, 2))
    if not candidates:
        return []

    doc_emb = sbert.encode([doc_text], convert_to_tensor=True)[0]
    cand_emb = sbert.encode(candidates, convert_to_tensor=True)
    sims = util.cos_sim(doc_emb, cand_emb).cpu().numpy().ravel()
    ranked = [c for c, _ in sorted(zip(candidates, sims), key=lambda x: x[1], reverse=True)]
    # de-duplicate while preserving order
    seen, result = set(), []
    for w in ranked:
        if w not in seen:
            seen.add(w)
            result.append(w)
        if len(result) >= top_n:
            break
    return result

def combine_keywords(tfidf_list: list[str], ctx_list: list[str], top_n: int = 20) -> list[str]:
    # prioritize contextual keywords, then fill with TF-IDF uniques
    combined, seen = [], set()
    for w in ctx_list + tfidf_list:
        if w not in seen:
            seen.add(w)
            combined.append(w)
        if len(combined) >= top_n:
            break
    return combined

# ---------- Routes ----------
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", standards=standards, selected=None, results=None, error=None)

@app.route("/analyze", methods=["POST"])
def analyze():
    std = request.form.get("standard", "").strip()
    pdf = request.files.get("bank_pdf")

    if not std:
        return render_template("index.html", standards=standards, selected=None, results=None,
                               error="Please select a standard.")
    if not pdf or not allowed_file(pdf.filename):
        return render_template("index.html", standards=standards, selected={"standard": std}, results=None,
                               error="Please upload a .pdf bank ESG report.")

    # Save upload
    fname = secure_filename(pdf.filename)
    fpath = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    pdf.save(fpath)

    # Read + clean
    raw = read_pdf_text(fpath)
    cleaned = clean_text(raw)

    # Keywords
    tf = tfidf_keywords(cleaned, top_n=15)
    ctx = contextual_keywords(cleaned, top_n=15, candidate_pool=80)
    combined = combine_keywords(tf, ctx, top_n=20)

    # Render
    return render_template(
        "index.html",
        standards=standards,
        selected={"standard": std},
        results={
            "filename": fname,
            "standard": std,
            "tfidf": tf,
            "contextual": ctx,
            "combined": combined,
            "sample": cleaned[:1000] + ("..." if len(cleaned) > 1000 else "")
        },
        error=None
    )

if __name__ == "__main__":
    app.run(debug=True)
