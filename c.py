import os
from vosk import Model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "vosk-model-en-us-0.22")

m = Model(MODEL_PATH)

print("✅ Model loaded successfully from:", MODEL_PATH)
