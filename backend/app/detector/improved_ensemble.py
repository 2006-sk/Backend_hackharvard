"""
Improved Ensemble Scam Detector
Enhanced with better feature engineering and threshold optimization
"""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib
import os
import re
from typing import Dict, Tuple, List
from .advanced_scam_detector import AdvancedScamDetector
from ..scam_model import get_model

class ImprovedEnsembleDetector:
    """
    Improved ensemble with better feature engineering and threshold optimization
    """
    
    def __init__(self, ensemble_model_path: str = "models/improved_ensemble_weights.joblib"):
        self.advanced_detector = AdvancedScamDetector()
        self.ml_model = get_model()
        self.ensemble_model_path = ensemble_model_path
        self.ensemble_model = None
        self.is_trained = False
        self.optimal_threshold = 0.5  # Will be optimized during training
        
        # Load pre-trained ensemble weights if available
        self._load_ensemble_model()
    
    def _load_ensemble_model(self):
        """Load pre-trained ensemble weights"""
        try:
            if os.path.exists(self.ensemble_model_path):
                model_data = joblib.load(self.ensemble_model_path)
                self.ensemble_model = model_data['model']
                self.optimal_threshold = model_data.get('threshold', 0.5)
                self.is_trained = True
                print(f"✅ Loaded improved ensemble model from {self.ensemble_model_path}")
            else:
                self.ensemble_model = LogisticRegression(random_state=42)
                self.is_trained = False
                print("⚠️ No pre-trained improved ensemble model found")
        except Exception as e:
            print(f"❌ Error loading improved ensemble model: {e}")
            self.ensemble_model = LogisticRegression(random_state=42)
            self.is_trained = False
    
    def extract_enhanced_features(self, text: str, stream_sid: str = "improved_test") -> np.ndarray:
        """
        Extract enhanced features with better engineering
        """
        # Get advanced detector analysis
        advanced_analysis = self.advanced_detector.analyze_segment(stream_sid, text)
        
        # Get ML model prediction
        ml_result = self.ml_model.predict(text)
        
        # Enhanced feature engineering
        text_lower = text.lower()
        
        # 1. Basic scores
        advanced_base = advanced_analysis['base_risk']
        advanced_smoothed = advanced_analysis['smoothed_risk']
        ml_prob = ml_result['probability']
        
        # 2. Keyword match ratios (more informative than counts)
        high_risk_matches = advanced_analysis.get('high_risk_matches', [])
        medium_risk_matches = advanced_analysis.get('medium_risk_matches', [])
        safe_breaker_matches = advanced_analysis.get('safe_breaker_matches', [])
        
        high_risk_ratio = len(high_risk_matches) / max(len(text.split()), 1)
        medium_risk_ratio = len(medium_risk_matches) / max(len(text.split()), 1)
        
        # 3. Text characteristics
        text_length = len(text)
        word_count = len(text.split())
        sentence_count = len([s for s in text.split('.') if s.strip()])
        
        # 4. Urgency indicators
        urgency_words = ['immediately', 'urgent', 'today', 'now', 'asap', 'right away', 'instant', 'quickly']
        urgency_score = sum(1 for word in urgency_words if word in text_lower) / max(word_count, 1)
        
        # 5. Pressure tactics
        pressure_words = ['arrest', 'warrant', 'legal action', 'fine', 'penalty', 'suspended', 'closed', 'expire']
        pressure_score = sum(1 for word in pressure_words if word in text_lower) / max(word_count, 1)
        
        # 6. Payment methods (scam indicators)
        payment_words = ['gift card', 'bitcoin', 'western union', 'money gram', 'itunes', 'prepaid']
        payment_score = sum(1 for word in payment_words if word in text_lower)
        
        # 7. Authority claims
        authority_words = ['irs', 'fbi', 'microsoft', 'amazon', 'bank', 'government', 'police', 'court']
        authority_score = sum(1 for word in authority_words if word in text_lower)
        
        # 8. Enhanced money pattern detection (scam indicators)
        money_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',  # $1,000, $500.00
            r'\d+(?:\.\d{2})?\s*dollars?',  # 1000 dollars, 500.00 dollar
            r'wire me \$[\d,]+',  # "wire me $10000"
            r'send me \$[\d,]+',  # "send me $5000"
            r'transfer \$[\d,]+',  # "transfer $2000"
            r'pay \$[\d,]+',  # "pay $1000"
            r'owe \$[\d,]+',  # "owe $500"
            r'fine of \$[\d,]+',  # "fine of $2000"
            r'fee of \$[\d,]+',  # "fee of $500"
            r'penalty of \$[\d,]+',  # "penalty of $1000"
            r'charge of \$[\d,]+',  # "charge of $300"
        ]
        money_matches = sum(len(re.findall(pattern, text_lower)) for pattern in money_patterns)
        
        # 9. Phone number requests
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|phone|call|number'
        phone_score = len(re.findall(phone_pattern, text_lower))
        
        # 10. Risk band encoding
        risk_band_encoded = self._encode_risk_band(advanced_analysis['risk_band'])
        
        # 11. Confidence indicators
        confidence_words = ['guaranteed', 'promise', 'sure', 'certain', 'guarantee']
        confidence_score = sum(1 for word in confidence_words if word in text_lower) / max(word_count, 1)
        
        # 12. Legitimacy indicators
        legitimacy_words = ['verify', 'confirm', 'security', 'protection', 'assistance', 'support']
        legitimacy_score = sum(1 for word in legitimacy_words if word in text_lower) / max(word_count, 1)
        
        # 13. Direct money request patterns (high scam indicator)
        direct_money_patterns = [
            r'wire me \$[\d,]+',  # "wire me $10000"
            r'send me \$[\d,]+',  # "send me $5000" 
            r'transfer me \$[\d,]+',  # "transfer me $2000"
            r'pay me \$[\d,]+',  # "pay me $1000"
            r'give me \$[\d,]+',  # "give me $500"
        ]
        direct_money_requests = sum(len(re.findall(pattern, text_lower)) for pattern in direct_money_patterns)
        
        # 14. Urgent money requests (very high scam indicator)
        urgent_money_patterns = [
            r'wire.*\$[\d,]+.*asap',  # "wire $5000 asap"
            r'send.*\$[\d,]+.*immediately',  # "send $2000 immediately"
            r'pay.*\$[\d,]+.*right now',  # "pay $1000 right now"
            r'transfer.*\$[\d,]+.*today',  # "transfer $3000 today"
        ]
        urgent_money_requests = sum(len(re.findall(pattern, text_lower)) for pattern in urgent_money_patterns)
        
        # Combine all features
        features = np.array([
            advanced_base,                    # 0: Advanced base risk
            advanced_smoothed,               # 1: Advanced smoothed risk
            ml_prob,                         # 2: ML probability
            risk_band_encoded,               # 3: Risk band
            high_risk_ratio,                 # 4: High risk keyword ratio
            medium_risk_ratio,               # 5: Medium risk keyword ratio
            min(text_length / 500.0, 1.0),   # 6: Normalized text length
            min(word_count / 50.0, 1.0),     # 7: Normalized word count
            min(sentence_count / 10.0, 1.0), # 8: Normalized sentence count
            urgency_score,                   # 9: Urgency score
            pressure_score,                  # 10: Pressure score
            min(payment_score / 3.0, 1.0),   # 11: Payment method score
            min(authority_score / 5.0, 1.0), # 12: Authority score
            min(money_matches / 3.0, 1.0),   # 13: Money mentions
            min(phone_score / 5.0, 1.0),     # 14: Phone number score
            confidence_score,                # 15: Confidence score
            legitimacy_score,                # 16: Legitimacy score
            min(direct_money_requests, 1.0), # 17: Direct money requests
            min(urgent_money_requests, 1.0), # 18: Urgent money requests
        ])
        
        return features.reshape(1, -1)
    
    def _encode_risk_band(self, risk_band: str) -> int:
        """Encode risk band as numerical value"""
        band_mapping = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        return band_mapping.get(risk_band, 0)
    
    def predict(self, text: str, stream_sid: str = "improved_test") -> Dict:
        """
        Make improved ensemble prediction
        """
        # Extract enhanced features
        features = self.extract_enhanced_features(text, stream_sid)
        
        if not self.is_trained:
            # If not trained, use improved weighted average
            advanced_analysis = self.advanced_detector.analyze_segment(stream_sid, text)
            ml_result = self.ml_model.predict(text)
            
            # Enhanced weighting based on feature analysis
            advanced_weight = 0.7  # Higher weight for advanced detector
            ml_weight = 0.3
            
            # Adjust weights based on confidence
            if advanced_analysis['base_risk'] > 0.8:
                advanced_weight = 0.8  # Trust advanced detector more for high-risk
            elif advanced_analysis['base_risk'] < 0.2:
                advanced_weight = 0.5  # Trust ML more for low-risk
            
            ensemble_score = advanced_weight * advanced_analysis['smoothed_risk'] + ml_weight * ml_result['probability']
            
            return {
                "ensemble_score": ensemble_score,
                "advanced_score": advanced_analysis['smoothed_risk'],
                "ml_score": ml_result['probability'],
                "prediction": "scam" if ensemble_score >= 0.6 else ("suspicious" if ensemble_score >= 0.4 else "safe"),
                "risk_band": "HIGH" if ensemble_score >= 0.6 else ("MEDIUM" if ensemble_score >= 0.4 else "LOW"),
                "method": "improved_weighted_average",
                "is_trained": False,
                "features": features[0].tolist()
            }
        else:
            # Use trained ensemble model with optimized threshold
            ensemble_prob = self.ensemble_model.predict_proba(features)[0][1]
            
            return {
                "ensemble_score": ensemble_prob,
                "advanced_score": features[0][1],  # Smoothed risk
                "ml_score": features[0][2],        # ML probability
                "prediction": "scam" if ensemble_prob >= self.optimal_threshold else ("suspicious" if ensemble_prob >= 0.4 else "safe"),
                "risk_band": "HIGH" if ensemble_prob >= self.optimal_threshold else ("MEDIUM" if ensemble_prob >= 0.4 else "LOW"),
                "method": "improved_logistic_regression",
                "is_trained": True,
                "optimal_threshold": self.optimal_threshold,
                "feature_importance": self._get_feature_importance(),
                "features": features[0].tolist()
            }
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if not self.is_trained or not hasattr(self.ensemble_model, 'coef_'):
            return {}
        
        feature_names = [
            "advanced_base", "advanced_smoothed", "ml_probability", "risk_band",
            "high_risk_ratio", "medium_risk_ratio", "text_length", "word_count",
            "sentence_count", "urgency_score", "pressure_score", "payment_score",
            "authority_score", "money_matches", "phone_score", "confidence_score",
            "legitimacy_score", "direct_money_requests", "urgent_money_requests"
        ]
        
        importance = {}
        for i, name in enumerate(feature_names):
            if i < len(self.ensemble_model.coef_[0]):
                importance[name] = float(self.ensemble_model.coef_[0][i])
        
        return importance
    
    def create_improved_training_data(self) -> List[Tuple[str, int]]:
        """Create improved training data with better examples"""
        return [
            # Clear Scams (label = 1)
            ("IRS officer calling about tax debt, pay immediately with gift cards or face arrest", 1),
            ("Congratulations! You won $1 million lottery! Send $500 processing fee via Western Union", 1),
            ("Microsoft support detected virus on your computer, grant remote access now", 1),
            ("Your Amazon account will be charged $500, provide credit card to cancel", 1),
            ("FBI calling about social security fraud, pay $2000 in iTunes gift cards immediately", 1),
            ("Your bank account is compromised, verify SSN and PIN to secure funds", 1),
            ("Vehicle warranty expiring today, press 1 now or lose coverage forever", 1),
            ("Government grant $10,000 available, pay $200 administrative fee first", 1),
            ("Debt collector calling about $5000 loan, pay now or face wage garnishment", 1),
            ("Social Security benefits suspended, verify bank account details immediately", 1),
            ("Your computer has been infected with ransomware, pay Bitcoin to decrypt files", 1),
            ("Windows Defender detected Trojan horse malware, download our security software", 1),
            ("URGENT: Your account will be closed TODAY unless you call immediately!", 1),
            ("This is your FINAL WARNING about serious consequences of not paying", 1),
            ("Don't hang up! This is extremely important for your financial security", 1),
            
            # Enhanced Scam Patterns with Money Requests
            ("Wire me $10,000 asap or face arrest warrant", 1),
            ("Send me $5,000 immediately via Western Union", 1),
            ("Transfer $2,000 to this account right now", 1),
            ("Pay $1,500 fine today or go to jail", 1),
            ("Owe $3,000 in taxes, pay now with gift cards", 1),
            ("Send $500 processing fee to claim your prize", 1),
            ("Wire transfer $8,000 to secure your account", 1),
            ("Pay $1,200 administrative fee for government grant", 1),
            ("Transfer $4,000 immediately to avoid criminal charges", 1),
            ("Send $600 via Bitcoin to unlock your computer", 1),
            
            # Amazon Gift Scam Patterns (from real transcript)
            ("I would actually to offer you a gift. Guard of thousand dollars from amazon services", 1),
            ("For that, you just need to tell me your phone number and then receive an otp", 1),
            ("After that, i can easily transfer that money into your account", 1),
            ("Amazon gift of thousand dollars, just need your phone number and otp", 1),
            ("Transfer money into your account after you provide phone number and otp", 1),
            ("Amazon services offering thousand dollars gift, need your phone and otp", 1),
            ("Gift from amazon, provide phone number and otp to transfer money", 1),
            
            # Clear Legitimate Calls (label = 0)
            ("Customer service calling to verify recent transactions for security purposes", 0),
            ("Microsoft support following up on your Office 365 purchase satisfaction", 0),
            ("IRS taxpayer assistance center calling about your tax return questions", 0),
            ("Amazon customer service confirming delivery address for your order", 0),
            ("Bank fraud prevention department verifying suspicious transactions with you", 0),
            ("Insurance company calling about policy renewal options and coverage", 0),
            ("DMV calling to remind you about vehicle registration renewal deadline", 0),
            ("Credit card company fraud department verifying recent authorized charges", 0),
            ("FBI public information office conducting routine community safety check", 0),
            ("Social Security Administration calling about benefits application processing", 0),
            ("IT support calling about scheduled system maintenance on your server", 0),
            ("Software update available for your operating system, download from official site", 0),
            ("Cybersecurity team calling about potential data breach investigation", 0),
            ("We're sorry to bother you, but this is important for your account safety", 0),
            ("Thank you for your patience as we resolve this matter together", 0),
            
            # Additional Legitimate Examples (to reduce false positives)
            ("Hello, this is Sarah from customer service at your bank", 0),
            ("We are calling to verify some recent transactions for security purposes", 0),
            ("This is a routine call to confirm your account information", 0),
            ("We want to make sure your account is protected from fraud", 0),
            ("Please verify your recent purchases to help us secure your account", 0),
            ("Customer protection team calling about your account security", 0),
            ("We're calling to help you with your account verification", 0),
            ("This is a courtesy call about your recent account activity", 0),
            ("We want to confirm some transactions for your protection", 0),
            ("Security team calling to verify your recent account usage", 0),
            
            # Edge Cases - Legitimate (label = 0)
            ("This is the fraud department calling about your account verification", 0),
            ("We're calling from Microsoft about a security issue with your account", 0),
            ("IRS calling about your tax refund, we need bank details to process it", 0),
            ("Fraud prevention team calling to verify recent account activity", 0),
            ("Security department calling about unusual login attempts on your account", 0),
            ("Customer protection team calling about potential unauthorized charges", 0),
            
            # Edge Cases - Scam (label = 1)
            ("Fraud department needs your social security number to verify identity", 1),
            ("Microsoft detected malware, we need your credit card to fix it", 1),
            ("IRS calling about tax debt, pay immediately or face arrest warrant", 1),
            ("Security team calling about account breach, provide your PIN immediately", 1),
            ("Fraud prevention calling, we need your bank account number to secure it", 1),
            ("Customer protection calling, verify your account with your SSN now", 1),
        ]
    
    def train_improved_ensemble(self, training_data: List[Tuple[str, int]] = None) -> Dict:
        """Train the improved ensemble model"""
        if training_data is None:
            training_data = self.create_improved_training_data()
        
        print(f"🎯 Training improved ensemble model on {len(training_data)} samples...")
        
        # Extract enhanced features
        X = []
        y = []
        
        for text, label in training_data:
            try:
                features = self.extract_enhanced_features(text, f"train_{len(X)}")
                X.append(features[0])
                y.append(label)
            except Exception as e:
                print(f"⚠️ Skipping training sample: {e}")
                continue
        
        if len(X) < 10:
            return {"success": False, "message": "Insufficient training data"}
        
        X = np.array(X)
        y = np.array(y)
        
        # Train logistic regression
        self.ensemble_model = LogisticRegression(random_state=42, max_iter=1000)
        self.ensemble_model.fit(X, y)
        
        # Optimize threshold using validation
        y_prob = self.ensemble_model.predict_proba(X)[:, 1]
        self.optimal_threshold = self._optimize_threshold(y, y_prob)
        
        # Calculate accuracy with optimized threshold
        y_pred = (y_prob >= self.optimal_threshold).astype(int)
        accuracy = np.mean(y_pred == y)
        
        print(f"✅ Improved ensemble trained - Accuracy: {accuracy:.3f}, Optimal threshold: {self.optimal_threshold:.3f}")
        
        # Save model
        os.makedirs(os.path.dirname(self.ensemble_model_path), exist_ok=True)
        model_data = {
            'model': self.ensemble_model,
            'threshold': self.optimal_threshold,
            'feature_names': [
                "advanced_base", "advanced_smoothed", "ml_probability", "risk_band",
                "high_risk_ratio", "medium_risk_ratio", "text_length", "word_count",
                "sentence_count", "urgency_score", "pressure_score", "payment_score",
                "authority_score", "money_matches", "phone_score", "confidence_score",
                "legitimacy_score", "direct_money_requests", "urgent_money_requests"
            ]
        }
        joblib.dump(model_data, self.ensemble_model_path)
        self.is_trained = True
        
        return {
            "success": True,
            "accuracy": accuracy,
            "optimal_threshold": self.optimal_threshold,
            "training_samples": len(X),
            "feature_importance": self._get_feature_importance()
        }
    
    def _optimize_threshold(self, y_true: np.ndarray, y_prob: np.ndarray) -> float:
        """Optimize classification threshold for better precision/recall balance"""
        from sklearn.metrics import precision_recall_curve
        
        precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
        
        # Find threshold that maximizes F1 score
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
        best_idx = np.argmax(f1_scores)
        
        return thresholds[best_idx] if best_idx < len(thresholds) else 0.5

# Global improved ensemble detector
_improved_ensemble_detector = None

def get_improved_ensemble_detector() -> ImprovedEnsembleDetector:
    """Get singleton instance of improved ensemble detector"""
    global _improved_ensemble_detector
    if _improved_ensemble_detector is None:
        _improved_ensemble_detector = ImprovedEnsembleDetector()
    return _improved_ensemble_detector

def analyze_with_improved_ensemble(text: str, stream_sid: str = "improved_test") -> Dict:
    """Convenience function for improved ensemble analysis"""
    detector = get_improved_ensemble_detector()
    return detector.predict(text, stream_sid)
