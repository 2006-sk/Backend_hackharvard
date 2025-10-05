from app.scam_model import get_model

def predict_scam_probability(text: str):
    """
    Predict scam probability using the trained ML model
    
    Args:
        text: Input text to analyze
        
    Returns:
        float: Probability score between 0.0 and 1.0
    """
    try:
        model = get_model()
        result = model.predict(text)
        return result["probability"]
    except Exception as e:
        print(f"❌ ML model prediction error: {e}")
        return 0.0
