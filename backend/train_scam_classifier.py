# train_scam_classifier.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score, precision_score, recall_score, f1_score, accuracy_score
from sentence_transformers import SentenceTransformer
import joblib
import os

# === CONFIG ===
DATA_PATH = "data/scam_dataset_balanced.csv"
MODEL_OUT = "models/scam_clf.joblib"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # fast + accurate

# === LOAD DATA ===
print("Loading dataset from", DATA_PATH)

df = pd.read_csv(DATA_PATH)

if "text" not in df.columns or "label" not in df.columns:
    raise ValueError("Dataset must have columns: 'text' and 'label'")

df.dropna(subset=["text", "label"], inplace=True)
df["text"] = df["text"].astype(str)
df["label"] = df["label"].astype(int)

print(f"Loaded {len(df)} samples ({df['label'].sum()} scams, {len(df) - df['label'].sum()} safe)")

# === TRAIN/TEST SPLIT ===
X_train, X_test, y_train, y_test = train_test_split(
    df["text"].tolist(),
    df["label"].tolist(),
    test_size=0.2,
    random_state=42,
    stratify=df["label"]
)

# === EMBEDDINGS ===
print(f"Loading embedding model: {EMBED_MODEL}")
embedder = SentenceTransformer(EMBED_MODEL)

print("Computing embeddings...")
X_train_emb = embedder.encode(X_train, convert_to_numpy=True, show_progress_bar=True)
X_test_emb = embedder.encode(X_test, convert_to_numpy=True, show_progress_bar=True)

# === MODEL TRAINING ===
print("🚀 Training Logistic Regression classifier...")
clf = LogisticRegression(max_iter=1000, class_weight="balanced")
clf.fit(X_train_emb, y_train)

# === EVALUATION ===
print("Evaluating model...")
y_pred = clf.predict(X_test_emb)
y_prob = clf.predict_proba(X_test_emb)[:, 1]

# Metrics
acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred)
rec = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_prob)

print("\n=== Classification Report ===")
print(classification_report(y_test, y_pred, digits=3))
print(f"ROC-AUC: {auc:.3f}")
print(f"Accuracy: {acc:.3f}")
print(f"Precision: {prec:.3f}")
print(f"Recall: {rec:.3f}")
print(f"F1 Score: {f1:.3f}")

# === SAVE MODEL ===
os.makedirs("models", exist_ok=True)
joblib.dump({
    "clf": clf,
    "embed_model": EMBED_MODEL
}, MODEL_OUT)

print(f"\nModel saved to {MODEL_OUT}")
