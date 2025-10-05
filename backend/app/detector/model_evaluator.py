"""
Model Evaluation and Performance Analysis
Comprehensive evaluation of ensemble scam detection model
"""

import numpy as np
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score, 
    accuracy_score, confusion_matrix, classification_report,
    roc_curve, precision_recall_curve, average_precision_score
)
from sklearn.model_selection import cross_val_score, StratifiedKFold
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("⚠️ Matplotlib/Seaborn not available - plotting disabled")
from typing import Dict, List, Tuple, Any
import json
import os
from .ensemble_detector import EnsembleScamDetector

class ModelEvaluator:
    """
    Comprehensive model evaluation with multiple metrics and edge case testing
    """
    
    def __init__(self):
        self.ensemble_detector = EnsembleScamDetector()
        self.evaluation_results = {}
        
    def create_comprehensive_test_dataset(self) -> Tuple[List[Tuple[str, int]], Dict[str, List]]:
        """
        Create comprehensive test dataset with various edge cases
        """
        test_data = []
        edge_cases = {
            "obvious_scams": [],
            "legitimate_calls": [],
            "ambiguous_cases": [],
            "technical_terms": [],
            "emotional_language": [],
            "short_phrases": [],
            "long_complex": [],
            "mixed_language": [],
            "numbers_and_money": [],
            "urgency_pressure": []
        }
        
        # Obvious Scams (label = 1)
        obvious_scams = [
            ("IRS officer calling about tax debt, pay immediately with gift cards or face arrest", 1),
            ("Congratulations! You won $1 million lottery! Send $500 processing fee via Western Union", 1),
            ("Microsoft support detected virus on your computer, grant remote access now", 1),
            ("Your Amazon account will be charged $500, provide credit card to cancel", 1),
            ("FBI calling about social security fraud, pay $2000 in iTunes gift cards immediately", 1),
            ("Your bank account is compromised, verify SSN and PIN to secure funds", 1),
            ("Vehicle warranty expiring today, press 1 now or lose coverage forever", 1),
            ("Government grant of $10,000 available, pay $200 administrative fee first", 1),
            ("Debt collector calling about $5000 loan, pay now or face wage garnishment", 1),
            ("Social Security benefits suspended, verify bank account details immediately", 1),
        ]
        test_data.extend(obvious_scams)
        edge_cases["obvious_scams"] = obvious_scams
        
        # Legitimate Calls (label = 0)
        legitimate_calls = [
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
        ]
        test_data.extend(legitimate_calls)
        edge_cases["legitimate_calls"] = legitimate_calls
        
        # Ambiguous Cases (mixed labels - these are challenging)
        ambiguous_cases = [
            ("This is the fraud department calling about your account verification", 0),  # Legitimate
            ("Fraud department needs your social security number to verify identity", 1),  # Scam
            ("We're calling from Microsoft about a security issue with your account", 0),  # Legitimate
            ("Microsoft detected malware, we need your credit card to fix it", 1),  # Scam
            ("IRS calling about your tax refund, we need bank details to process it", 0),  # Legitimate
            ("IRS calling about tax debt, pay immediately or face arrest warrant", 1),  # Scam
        ]
        test_data.extend(ambiguous_cases)
        edge_cases["ambiguous_cases"] = ambiguous_cases
        
        # Technical Terms
        technical_terms = [
            ("Your computer has been infected with ransomware, pay Bitcoin to decrypt files", 1),
            ("Windows Defender detected Trojan horse malware, download our security software", 1),
            ("Your IP address has been compromised, we need remote access to secure it", 1),
            ("IT support calling about scheduled system maintenance on your server", 0),
            ("Software update available for your operating system, download from official site", 0),
            ("Cybersecurity team calling about potential data breach investigation", 0),
        ]
        test_data.extend(technical_terms)
        edge_cases["technical_terms"] = technical_terms
        
        # Emotional Language
        emotional_language = [
            ("URGENT: Your account will be closed TODAY unless you call immediately!", 1),
            ("This is your FINAL WARNING about the serious consequences of not paying", 1),
            ("Don't hang up! This is extremely important for your financial security", 1),
            ("We're sorry to bother you, but this is important for your account safety", 0),
            ("Thank you for your patience as we resolve this matter together", 0),
            ("We understand this might be concerning, let us help you verify everything", 0),
        ]
        test_data.extend(emotional_language)
        edge_cases["emotional_language"] = emotional_language
        
        # Short Phrases
        short_phrases = [
            ("IRS calling about taxes", 1),
            ("You owe money", 1),
            ("Pay now or arrested", 1),
            ("Customer service calling", 0),
            ("Account verification needed", 0),
            ("Thank you for calling", 0),
        ]
        test_data.extend(short_phrases)
        edge_cases["short_phrases"] = short_phrases
        
        # Long Complex Sentences
        long_complex = [
            ("This is Officer Johnson from the Internal Revenue Service calling regarding your outstanding tax liability of $5,000 which has been flagged for immediate collection due to non-payment and we are authorized to take legal action including but not limited to wage garnishment bank account seizure and property liens unless payment is received within 24 hours via gift cards", 1),
            ("We are calling from the customer service department at your financial institution to discuss some recent account activity that our fraud prevention team has identified as potentially suspicious and we would like to work with you to verify these transactions and ensure the security of your account", 0),
        ]
        test_data.extend(long_complex)
        edge_cases["long_complex"] = long_complex
        
        # Numbers and Money
        numbers_money = [
            ("You owe exactly $4,237.89 and must pay today or face legal action", 1),
            ("Send $500 in Bitcoin to wallet address 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa immediately", 1),
            ("Your refund of $1,234.56 is ready, but we need your bank routing number", 1),
            ("Your account balance shows $2,500.00, we're calling to verify recent transactions", 0),
            ("The monthly service fee is $9.99, would you like to discuss payment options?", 0),
            ("Your insurance premium of $156.78 is due next week, shall we process payment?", 0),
        ]
        test_data.extend(numbers_money)
        edge_cases["numbers_money"] = numbers_money
        
        # Urgency and Pressure
        urgency_pressure = [
            ("This must be resolved TODAY or your account will be permanently closed", 1),
            ("Time is running out, you have 30 minutes to prevent legal action", 1),
            ("Don't delay, this is your last chance to avoid serious consequences", 1),
            ("We need to resolve this quickly to protect your account from further issues", 0),
            ("Please call us back at your earliest convenience to discuss this matter", 0),
            ("No rush, take your time to verify this information when convenient", 0),
        ]
        test_data.extend(urgency_pressure)
        edge_cases["urgency_pressure"] = urgency_pressure
        
        return test_data, edge_cases
    
    def evaluate_model_comprehensive(self) -> Dict[str, Any]:
        """
        Comprehensive model evaluation with multiple metrics
        """
        print("🔍 Starting comprehensive model evaluation...")
        
        # Create test dataset
        test_data, edge_cases = self.create_comprehensive_test_dataset()
        
        # Extract features and predictions
        X = []
        y_true = []
        y_pred = []
        y_prob = []
        
        print(f"📊 Evaluating on {len(test_data)} test samples...")
        
        for text, true_label in test_data:
            try:
                # Get ensemble prediction
                result = self.ensemble_detector.predict(text, f"eval_{len(X)}")
                
                # Extract features for analysis
                features = self.ensemble_detector.extract_features(text, f"eval_{len(X)}")
                X.append(features[0])
                
                y_true.append(true_label)
                y_prob.append(result['ensemble_score'])
                
                # Convert probability to binary prediction
                pred_label = 1 if result['ensemble_score'] >= 0.5 else 0
                y_pred.append(pred_label)
                
            except Exception as e:
                print(f"⚠️ Error processing sample: {e}")
                continue
        
        if len(y_true) < 10:
            return {"error": "Insufficient valid test samples"}
        
        # Convert to numpy arrays
        X = np.array(X)
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        y_prob = np.array(y_prob)
        
        # Calculate comprehensive metrics
        metrics = self._calculate_all_metrics(y_true, y_pred, y_prob)
        
        # Edge case analysis
        edge_case_results = self._analyze_edge_cases(edge_cases)
        
        # Cross-validation if model is trained
        cv_results = self._cross_validate_model(X, y_true) if self.ensemble_detector.is_trained else {}
        
        # Feature importance analysis
        feature_importance = self.ensemble_detector._get_feature_importance() if self.ensemble_detector.is_trained else {}
        
        self.evaluation_results = {
            "overall_metrics": metrics,
            "edge_case_analysis": edge_case_results,
            "cross_validation": cv_results,
            "feature_importance": feature_importance,
            "test_samples": len(y_true),
            "model_trained": self.ensemble_detector.is_trained
        }
        
        return self.evaluation_results
    
    def _calculate_all_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
        """Calculate all evaluation metrics"""
        metrics = {}
        
        # Basic classification metrics
        metrics['accuracy'] = accuracy_score(y_true, y_pred)
        metrics['precision'] = precision_score(y_true, y_pred, zero_division=0)
        metrics['recall'] = recall_score(y_true, y_pred, zero_division=0)
        metrics['f1_score'] = f1_score(y_true, y_pred, zero_division=0)
        
        # ROC AUC
        try:
            metrics['roc_auc'] = roc_auc_score(y_true, y_prob)
        except ValueError:
            metrics['roc_auc'] = 0.0
        
        # Precision-Recall AUC
        try:
            metrics['pr_auc'] = average_precision_score(y_true, y_prob)
        except ValueError:
            metrics['pr_auc'] = 0.0
        
        # Confusion Matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = {
            'true_negatives': int(cm[0, 0]),
            'false_positives': int(cm[0, 1]),
            'false_negatives': int(cm[1, 0]),
            'true_positives': int(cm[1, 1])
        }
        
        # Additional metrics
        metrics['specificity'] = cm[0, 0] / (cm[0, 0] + cm[0, 1]) if (cm[0, 0] + cm[0, 1]) > 0 else 0
        metrics['sensitivity'] = cm[1, 1] / (cm[1, 1] + cm[1, 0]) if (cm[1, 1] + cm[1, 0]) > 0 else 0
        
        return metrics
    
    def _analyze_edge_cases(self, edge_cases: Dict[str, List]) -> Dict[str, Dict]:
        """Analyze performance on different edge case categories"""
        edge_results = {}
        
        for category, samples in edge_cases.items():
            if not samples:
                continue
                
            correct = 0
            total = len(samples)
            predictions = []
            
            for text, true_label in samples:
                try:
                    result = self.ensemble_detector.predict(text, f"edge_{category}_{len(predictions)}")
                    pred_label = 1 if result['ensemble_score'] >= 0.5 else 0
                    predictions.append({
                        'text': text[:50] + "...",
                        'true_label': true_label,
                        'predicted_label': pred_label,
                        'probability': result['ensemble_score'],
                        'correct': pred_label == true_label
                    })
                    
                    if pred_label == true_label:
                        correct += 1
                        
                except Exception as e:
                    predictions.append({
                        'text': text[:50] + "...",
                        'error': str(e)
                    })
            
            edge_results[category] = {
                'accuracy': correct / total if total > 0 else 0,
                'total_samples': total,
                'correct_predictions': correct,
                'predictions': predictions
            }
        
        return edge_results
    
    def _cross_validate_model(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Perform cross-validation if model is trained"""
        if not self.ensemble_detector.is_trained:
            return {"error": "Model not trained"}
        
        try:
            # Use StratifiedKFold for balanced cross-validation
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            
            # Cross-validate accuracy
            cv_scores = cross_val_score(
                self.ensemble_detector.ensemble_model, 
                X, y, 
                cv=cv, 
                scoring='accuracy'
            )
            
            return {
                'cv_accuracy_mean': float(cv_scores.mean()),
                'cv_accuracy_std': float(cv_scores.std()),
                'cv_accuracy_scores': cv_scores.tolist()
            }
            
        except Exception as e:
            return {"error": f"Cross-validation failed: {str(e)}"}
    
    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report"""
        if not self.evaluation_results:
            return "No evaluation results available. Run evaluate_model_comprehensive() first."
        
        report = []
        report.append("=" * 60)
        report.append("SCAM DETECTION MODEL PERFORMANCE REPORT")
        report.append("=" * 60)
        
        # Overall Metrics
        metrics = self.evaluation_results['overall_metrics']
        report.append(f"\n📊 OVERALL PERFORMANCE METRICS")
        report.append("-" * 40)
        report.append(f"Accuracy:           {metrics['accuracy']:.3f}")
        report.append(f"Precision:          {metrics['precision']:.3f}")
        report.append(f"Recall:             {metrics['recall']:.3f}")
        report.append(f"F1-Score:           {metrics['f1_score']:.3f}")
        report.append(f"ROC AUC:            {metrics['roc_auc']:.3f}")
        report.append(f"PR AUC:             {metrics['pr_auc']:.3f}")
        report.append(f"Specificity:        {metrics['specificity']:.3f}")
        report.append(f"Sensitivity:        {metrics['sensitivity']:.3f}")
        
        # Confusion Matrix
        cm = metrics['confusion_matrix']
        report.append(f"\n📈 CONFUSION MATRIX")
        report.append("-" * 40)
        report.append(f"True Negatives:     {cm['true_negatives']}")
        report.append(f"False Positives:    {cm['false_positives']}")
        report.append(f"False Negatives:    {cm['false_negatives']}")
        report.append(f"True Positives:     {cm['true_positives']}")
        
        # Edge Case Analysis
        report.append(f"\n🎯 EDGE CASE PERFORMANCE")
        report.append("-" * 40)
        edge_results = self.evaluation_results['edge_case_analysis']
        for category, results in edge_results.items():
            if isinstance(results, dict) and 'accuracy' in results:
                report.append(f"{category.replace('_', ' ').title():<25}: {results['accuracy']:.3f} ({results['correct_predictions']}/{results['total_samples']})")
        
        # Feature Importance
        if self.evaluation_results['feature_importance']:
            report.append(f"\n🔍 FEATURE IMPORTANCE")
            report.append("-" * 40)
            for feature, importance in self.evaluation_results['feature_importance'].items():
                report.append(f"{feature.replace('_', ' ').title():<25}: {importance:+.3f}")
        
        # Cross-Validation
        if self.evaluation_results['cross_validation'] and 'error' not in self.evaluation_results['cross_validation']:
            cv = self.evaluation_results['cross_validation']
            report.append(f"\n🔄 CROSS-VALIDATION")
            report.append("-" * 40)
            report.append(f"CV Accuracy Mean:   {cv['cv_accuracy_mean']:.3f}")
            report.append(f"CV Accuracy Std:    {cv['cv_accuracy_std']:.3f}")
        
        # Recommendations
        report.append(f"\n💡 RECOMMENDATIONS")
        report.append("-" * 40)
        if metrics['accuracy'] < 0.8:
            report.append("• Consider collecting more training data")
        if metrics['precision'] < 0.7:
            report.append("• High false positive rate - tune threshold or improve feature engineering")
        if metrics['recall'] < 0.7:
            report.append("• High false negative rate - model may be missing scams")
        if metrics['roc_auc'] < 0.8:
            report.append("• Model discrimination could be improved")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_evaluation_results(self, filename: str = "model_evaluation_results.json"):
        """Save evaluation results to JSON file"""
        if not self.evaluation_results:
            print("No evaluation results to save")
            return
        
        # Convert numpy arrays to lists for JSON serialization
        serializable_results = json.loads(json.dumps(self.evaluation_results, default=str))
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"📁 Evaluation results saved to {filename}")

# Convenience function
def evaluate_ensemble_model() -> Dict[str, Any]:
    """Evaluate the ensemble model comprehensively"""
    evaluator = ModelEvaluator()
    results = evaluator.evaluate_model_comprehensive()
    
    # Generate and print report
    report = evaluator.generate_performance_report()
    print(report)
    
    # Save results
    evaluator.save_evaluation_results()
    
    return results
