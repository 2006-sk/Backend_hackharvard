"""
Ensemble Scam Detector
Combines AdvancedScamDetector (keyword-based) and ML model using logistic regression
"""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib
import os
from typing import Dict, Tuple, List
from .advanced_scam_detector import AdvancedScamDetector
from ..scam_model import get_model

class EnsembleScamDetector:
    """
    Ensemble detector that combines keyword-based detection with ML model
    Uses logistic regression to learn optimal weights for each approach
    """
    
    def __init__(self, ensemble_model_path: str = "models/ensemble_weights.joblib"):
        self.advanced_detector = AdvancedScamDetector()
        self.ml_model = get_model()
        self.ensemble_model_path = ensemble_model_path
        self.ensemble_model = None
        self.is_trained = False
        
        # Load pre-trained ensemble weights if available
        self._load_ensemble_model()
    
    def _load_ensemble_model(self):
        """Load pre-trained ensemble weights"""
        try:
            if os.path.exists(self.ensemble_model_path):
                self.ensemble_model = joblib.load(self.ensemble_model_path)
                self.is_trained = True
                print(f"✅ Loaded ensemble model from {self.ensemble_model_path}")
            else:
                # Initialize with default weights
                self.ensemble_model = LogisticRegression(random_state=42)
                self.is_trained = False
                print("⚠️ No pre-trained ensemble model found, using default weights")
        except Exception as e:
            print(f"❌ Error loading ensemble model: {e}")
            self.ensemble_model = LogisticRegression(random_state=42)
            self.is_trained = False
    
    def extract_features(self, text: str, stream_sid: str = "ensemble_test") -> np.ndarray:
        """
        Extract features from both detectors for ensemble training/prediction
        
        Features:
        1. Advanced detector base risk score
        2. Advanced detector smoothed risk score  
        3. Advanced detector risk band (encoded)
        4. Number of high-risk keyword matches
        5. Number of medium-risk keyword matches
        6. ML model probability
        7. Text length (normalized)
        8. Number of sentences
        """
        # Get advanced detector analysis
        advanced_analysis = self.advanced_detector.analyze_segment(stream_sid, text)
        
        # Get ML model prediction
        ml_result = self.ml_model.predict(text)
        
        # Extract features
        features = np.array([
            advanced_analysis['base_risk'],                    # 0: Base risk (0-1)
            advanced_analysis['smoothed_risk'],               # 1: Smoothed risk (0-1)
            self._encode_risk_band(advanced_analysis['risk_band']),  # 2: Risk band (0-2)
            len(advanced_analysis.get('high_risk_matches', [])),     # 3: High risk matches count
            len(advanced_analysis.get('medium_risk_matches', [])),   # 4: Medium risk matches count
            ml_result['probability'],                         # 5: ML model probability (0-1)
            min(len(text) / 500.0, 1.0),                     # 6: Text length (normalized to 0-1)
            len([s for s in text.split('.') if s.strip()]) / 10.0  # 7: Sentence count (normalized)
        ])
        
        return features.reshape(1, -1)  # Return as 2D array for sklearn
    
    def _encode_risk_band(self, risk_band: str) -> int:
        """Encode risk band as numerical value"""
        band_mapping = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        return band_mapping.get(risk_band, 0)
    
    def predict(self, text: str, stream_sid: str = "ensemble_test") -> Dict:
        """
        Make ensemble prediction combining both detectors
        """
        # Extract features
        features = self.extract_features(text, stream_sid)
        
        if not self.is_trained:
            # If not trained, use simple weighted average
            advanced_analysis = self.advanced_detector.analyze_segment(stream_sid, text)
            ml_result = self.ml_model.predict(text)
            
            # Default weights: 60% advanced detector, 40% ML model
            ensemble_score = 0.6 * advanced_analysis['smoothed_risk'] + 0.4 * ml_result['probability']
            
            return {
                "ensemble_score": ensemble_score,
                "advanced_score": advanced_analysis['smoothed_risk'],
                "ml_score": ml_result['probability'],
                "prediction": "scam" if ensemble_score >= 0.7 else ("suspicious" if ensemble_score >= 0.4 else "safe"),
                "risk_band": "HIGH" if ensemble_score >= 0.7 else ("MEDIUM" if ensemble_score >= 0.4 else "LOW"),
                "method": "weighted_average",
                "is_trained": False
            }
        else:
            # Use trained ensemble model
            ensemble_prob = self.ensemble_model.predict_proba(features)[0][1]
            
            return {
                "ensemble_score": ensemble_prob,
                "advanced_score": features[0][1],  # Smoothed risk from advanced detector
                "ml_score": features[0][5],        # ML model probability
                "prediction": "scam" if ensemble_prob >= 0.7 else ("suspicious" if ensemble_prob >= 0.4 else "safe"),
                "risk_band": "HIGH" if ensemble_prob >= 0.7 else ("MEDIUM" if ensemble_prob >= 0.4 else "LOW"),
                "method": "logistic_regression",
                "is_trained": True,
                "feature_importance": self._get_feature_importance()
            }
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained ensemble model"""
        if not self.is_trained or not hasattr(self.ensemble_model, 'coef_'):
            return {}
        
        feature_names = [
            "advanced_base_risk", "advanced_smoothed_risk", "risk_band", 
            "high_risk_matches", "medium_risk_matches", "ml_probability",
            "text_length", "sentence_count"
        ]
        
        importance = {}
        for i, name in enumerate(feature_names):
            importance[name] = float(self.ensemble_model.coef_[0][i])
        
        return importance
    
    def train_ensemble(self, training_data: List[Tuple[str, int]]) -> Dict:
        """
        Train the ensemble model on labeled data
        
        Args:
            training_data: List of (text, label) tuples where label is 0 (safe) or 1 (scam)
        """
        print(f"🎯 Training ensemble model on {len(training_data)} samples...")
        
        # Extract features for all training samples
        X = []
        y = []
        
        for text, label in training_data:
            try:
                features = self.extract_features(text, f"train_{len(X)}")
                X.append(features[0])  # Remove extra dimension
                y.append(label)
            except Exception as e:
                print(f"⚠️ Skipping training sample due to error: {e}")
                continue
        
        if len(X) < 10:
            print("❌ Not enough valid training samples (need at least 10)")
            return {"success": False, "message": "Insufficient training data"}
        
        X = np.array(X)
        y = np.array(y)
        
        # Train logistic regression
        self.ensemble_model = LogisticRegression(random_state=42, max_iter=1000)
        self.ensemble_model.fit(X, y)
        
        # Calculate accuracy
        y_pred = self.ensemble_model.predict(X)
        accuracy = np.mean(y_pred == y)
        
        print(f"✅ Ensemble model trained with accuracy: {accuracy:.3f}")
        
        # Save the trained model
        os.makedirs(os.path.dirname(self.ensemble_model_path), exist_ok=True)
        joblib.dump(self.ensemble_model, self.ensemble_model_path)
        self.is_trained = True
        
        # Generate classification report
        report = classification_report(y, y_pred, output_dict=True)
        
        return {
            "success": True,
            "accuracy": accuracy,
            "training_samples": len(X),
            "feature_importance": self._get_feature_importance(),
            "classification_report": report,
            "model_saved_to": self.ensemble_model_path
        }
    
    def create_sample_training_data(self) -> List[Tuple[str, int]]:
        """
        Create sample training data for ensemble training
        Returns list of (text, label) tuples
        """
        sample_data = [
            # Scam examples (label = 1)
            ("Hello, this is Officer Johnson from the IRS. You owe $5,000 in back taxes that must be paid immediately or we will arrest you today.", 1),
            ("Congratulations! You have won $1 million in the Publishers Clearing House sweepstakes! To claim your prize, send us a $500 processing fee.", 1),
            ("This is Microsoft technical support. Your computer has been infected with a virus. We need remote access to fix it.", 1),
            ("Your Amazon Prime subscription has expired and your account will be charged $500. Provide your credit card information to cancel.", 1),
            ("This is the FBI calling about your social security number. It has been used in illegal activities. Pay a fine of $2,000 in iTunes gift cards.", 1),
            ("Your vehicle's extended warranty is about to expire. Press 1 to speak with a warranty specialist or your coverage will be cancelled.", 1),
            ("We are calling from the Social Security Administration. Your benefits have been suspended. Verify your bank account details to restore them.", 1),
            ("This is a debt collector calling about an outstanding loan. You owe $3,000 and if you don't pay today, we will garnish your wages.", 1),
            ("Your bank account has been compromised. We need to verify your social security number and online banking password immediately.", 1),
            ("You have been selected for a special government grant program. We can give you $10,000 but you need to pay a $200 administrative fee first.", 1),
            
            # Legitimate examples (label = 0)
            ("Hello, this is Sarah from customer service at your bank. We're calling to verify some recent transactions for security purposes.", 0),
            ("Hi, I'm calling from Microsoft customer support regarding your recent purchase of Office 365. We want to make sure you're satisfied.", 0),
            ("Good morning, this is John from the IRS taxpayer assistance center. We received your tax return and wanted to follow up on a few questions.", 0),
            ("This is Amazon customer service calling about your recent order. We want to confirm the delivery address and make sure everything is set up correctly.", 0),
            ("Hi, I'm calling from your bank's fraud prevention department. We detected some potentially suspicious activity and want to verify these transactions.", 0),
            ("Hello, this is your insurance company calling about your policy renewal. We want to make sure you have the best coverage for your needs.", 0),
            ("This is the Department of Motor Vehicles calling about your vehicle registration renewal. We're contacting you to remind you about the upcoming expiration.", 0),
            ("Hi, I'm calling from your credit card company's fraud department. We want to verify some recent transactions to ensure they were authorized by you.", 0),
            ("Good afternoon, this is the FBI's public information office. We're conducting a routine security check and wanted to inform you about recent safety measures.", 0),
            ("Hello, this is the Social Security Administration calling about your recent application for benefits. We need to verify some information to ensure your application is processed correctly.", 0),
        ]
        
        return sample_data

# Global ensemble detector instance
_ensemble_detector = None

def get_ensemble_detector() -> EnsembleScamDetector:
    """Get singleton instance of ensemble detector"""
    global _ensemble_detector
    if _ensemble_detector is None:
        _ensemble_detector = EnsembleScamDetector()
    return _ensemble_detector

def analyze_with_ensemble(text: str, stream_sid: str = "ensemble_test") -> Dict:
    """Convenience function to analyze text with ensemble detector"""
    detector = get_ensemble_detector()
    return detector.predict(text, stream_sid)
