# app/scam_model.py
import joblib
from sentence_transformers import SentenceTransformer
import numpy as np
import os

MODEL_PATH = os.getenv("SCAM_MODEL_PATH", "models/scam_clf.joblib")

class ScamModel:
    def __init__(self, model_path=MODEL_PATH):
        print(f"🔍 Loading Scam Detection Model from {model_path}")
        model_data = joblib.load(model_path)
        self.clf = model_data["clf"]
        self.embed_name = model_data["embed_model"]
        self.embedder = SentenceTransformer(self.embed_name)
        print(f"✅ Loaded embedding model: {self.embed_name}")

    def predict(self, text: str):
        emb = self.embedder.encode([text], convert_to_numpy=True)
        prob = float(self.clf.predict_proba(emb)[0][1])
        label = int(prob >= 0.5)
        return {"label": label, "probability": round(prob, 3)}

# Singleton accessor
_model_instance = None
def get_model():
    global _model_instance
    if _model_instance is None:
        _model_instance = ScamModel()
    return _model_instance
