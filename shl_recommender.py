# SHL Semantic Recommendation System
# --------------------------------
# Prerequisites:
# pip install sentence-transformers scikit-learn fastapi uvicorn pandas beautifulsoup4 requests

import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup

# -----------------------------
# CONFIG
# -----------------------------
DATA_PATH = "assessments_all.json"  # your scraped file (519 items)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 10

# -----------------------------
# LOAD DATA
# -----------------------------
# Make path relative to this file
import os
DATA_PATH = os.path.join(os.path.dirname(__file__), "assessments_all.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Keep only required fields and clean text
records = []
for item in data:
    name = item.get("name", "").strip()
    if "solution" in name.lower():
        continue
    url = item.get("url", "").strip()
    desc = item.get("description", "").strip()
    if name and url and desc:
        records.append({
            "name": name,
            "url": url,
            "text": f"{name}. {desc}"
        })
        

print(f"Loaded {len(records)} assessments")

# -----------------------------
# GLOBAL VARIABLES
# -----------------------------
model = None
embeddings = None

def initialize_model():
    """Initialize model and embeddings (called once)"""
    global model, embeddings
    if model is None:
        model = SentenceTransformer(MODEL_NAME)
        assessment_texts = [r["text"] for r in records]
        embeddings = model.encode(assessment_texts, show_progress_bar=True)
        print(f"Initialized model with {len(embeddings)} embeddings")

# -----------------------------
# UTILS
# -----------------------------

def extract_text_from_url(url: str) -> str:
    """Fetch and extract visible text from a JD URL"""
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(t.strip() for t in soup.stripped_strings)
        return text
    except Exception:
        return ""


def recommend(query_text: str, k: int = TOP_K):
    initialize_model()  # Ensure model is loaded
    query_emb = model.encode([query_text])
    scores = cosine_similarity(query_emb, embeddings)[0]
    top_idx = np.argsort(scores)[-k:][::-1]

    results = []
    for i in top_idx:
        results.append({
            "assessment_name": records[i]["name"],
            "url": records[i]["url"],
            "score": float(scores[i])
        })
    return results


# -----------------------------
# CSV EVALUATION / PREDICTION
# -----------------------------


def recommend_for_query(query: str, k: int = TOP_K):
    results = recommend(query, k)
    return [r["assessment_name"] for r in results]


def find_query_column(df):
    for col in df.columns:
        if col.lower().strip() in ["query", "question", "jd", "job_description"]:
            return col
    return df.columns[0]  # fallback



def run_on_test_file(test_file_path: str, output_csv_path: str):

    # Load file
    if test_file_path.endswith(".xlsx"):
        df = pd.read_excel(test_file_path)
    else:
        df = pd.read_csv(
            test_file_path,
            encoding="latin1",
            engine="python",
            on_bad_lines="skip"
        )

    print("Columns found:", df.columns.tolist())

    query_col = find_query_column(df)
    print("Using query column:", query_col)

    predictions = []
    for query in df[query_col].astype(str):
        recs = recommend_for_query(query, TOP_K)
        predictions.append("; ".join(recs))

    df["recommended_assessments"] = predictions
    df.to_csv(output_csv_path, index=False)

    print(f"✅ Predictions saved to {output_csv_path}")


def evaluate_on_labeled_file(train_file_path: str, k: int = 10):

    # Load correctly
    if train_file_path.endswith(".xlsx"):
        df = pd.read_excel(train_file_path)
    else:
        df = pd.read_csv(
            train_file_path,
            encoding="latin1",
            engine="python",
            on_bad_lines="skip"
        )

    print("Columns found:", df.columns.tolist())

    query_col = find_query_column(df)

    # Identify ground truth column automatically
    gt_col = None
    for col in df.columns:
        if "recommend" in col.lower():
            gt_col = col
            break

    if gt_col is None:
        print("❌ No ground truth column found")
        return

    hits = 0
    total = 0

    for _, row in df.iterrows():
        query = str(row[query_col])

        true_assessments = [
            x.strip().lower()
            for x in str(row[gt_col]).split(";")
        ]

        preds = recommend_for_query(query, k)
        preds = [p.lower() for p in preds]

        if any(t in preds for t in true_assessments):
            hits += 1
        total += 1

    print(f"✅ Recall@{k}: {hits/total:.2f}")




# -----------------------------
# FASTAPI APP
# -----------------------------
app = FastAPI(title="SHL Assessment Recommender")

class QueryInput(BaseModel):
    query: str | None = None
    url: str | None = None


@app.post("/recommend")
def recommend_api(payload: QueryInput):
    if payload.url and payload.url.strip():

        text = extract_text_from_url(payload.url)
        if not text:
            return {"error": "Unable to extract text from URL"}
        query_text = text
    elif payload.query:
        query_text = payload.query
    else:
        return {"error": "Provide either query or url"}

    results = recommend(query_text, k=TOP_K)

    # Return ONLY required fields in tabular-friendly format
    return {
        "results": [
            {"Assessment name": r["assessment_name"], "URL": r["url"]}
            for r in results
        ]
    }

# -----------------------------
# LOCAL TEST (optional)
# -----------------------------
if __name__ == "__main__":
    q = "Data analyst with strong numerical and analytical reasoning"
    recs = recommend(q)
    for r in recs:
        print(r["assessment_name"], "->", r["url"])
    run_on_test_file(
    test_file_path="Gen_AI Dataset.xlsx",
    output_csv_path="test_predictions.csv"
)
    
    evaluate_on_labeled_file("Gen_AI Dataset.xlsx", k=10)



