from vosk import Model, KaldiRecognizer
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "vosk-model-en-us-0.22")

try:
    model = Model(MODEL_PATH)
    print(f"✅ Vosk model loaded from: {MODEL_PATH}")
except Exception as e:
    raise RuntimeError(f"❌ Failed to load Vosk model from {MODEL_PATH}. Error: {e}")

def get_transcriber(sample_rate: int):
    """Return a recognizer object for the given sample rate"""
    return KaldiRecognizer(model, sample_rate)
