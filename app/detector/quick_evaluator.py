"""
Quick Model Evaluation
Fast evaluation focusing on key metrics and edge cases
"""

import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from typing import Dict, List, Tuple
from .ensemble_detector import EnsembleScamDetector

class QuickEvaluator:
    """Fast model evaluation for quick performance checks"""
    
    def __init__(self):
        self.ensemble_detector = EnsembleScamDetector()
    
    def create_quick_test_dataset(self) -> List[Tuple[str, int]]:
        """Create a smaller, focused test dataset"""
        return [
            # Obvious Scams (label = 1)
            ("IRS calling about tax debt, pay immediately with gift cards or face arrest", 1),
            ("Congratulations! You won $1 million lottery! Send $500 processing fee", 1),
            ("Microsoft support detected virus, grant remote access now", 1),
            ("Your Amazon account will be charged $500, provide credit card to cancel", 1),
            ("FBI calling about social security fraud, pay $2000 in iTunes gift cards", 1),
            ("Your bank account is compromised, verify SSN and PIN immediately", 1),
            ("Vehicle warranty expiring today, press 1 now or lose coverage", 1),
            ("Government grant $10,000 available, pay $200 administrative fee first", 1),
            ("Debt collector calling about $5000 loan, pay now or face wage garnishment", 1),
            ("Social Security benefits suspended, verify bank account details now", 1),
            
            # Legitimate Calls (label = 0)
            ("Customer service calling to verify recent transactions for security", 0),
            ("Microsoft support following up on your Office 365 purchase", 0),
            ("IRS taxpayer assistance calling about your tax return questions", 0),
            ("Amazon customer service confirming delivery address for your order", 0),
            ("Bank fraud prevention verifying suspicious transactions with you", 0),
            ("Insurance company calling about policy renewal options", 0),
            ("DMV calling to remind about vehicle registration renewal", 0),
            ("Credit card fraud department verifying recent authorized charges", 0),
            ("FBI public information office conducting routine safety check", 0),
            ("Social Security Administration calling about benefits application", 0),
            
            # Edge Cases
            ("This is the fraud department calling about account verification", 0),
            ("Fraud department needs your social security number to verify identity", 1),
            ("We're calling from Microsoft about a security issue with your account", 0),
            ("Microsoft detected malware, we need your credit card to fix it", 1),
            ("IRS calling about your tax refund, we need bank details to process", 0),
            ("IRS calling about tax debt, pay immediately or face arrest warrant", 1),
        ]
    
    def evaluate_quick(self) -> Dict:
        """Quick evaluation with key metrics"""
        print("🚀 Running quick model evaluation...")
        
        test_data = self.create_quick_test_dataset()
        
        y_true = []
        y_pred = []
        y_prob = []
        predictions = []
        
        for i, (text, true_label) in enumerate(test_data):
            try:
                result = self.ensemble_detector.predict(text, f"quick_eval_{i}")
                
                y_true.append(true_label)
                y_prob.append(result['ensemble_score'])
                
                # Convert probability to binary prediction
                pred_label = 1 if result['ensemble_score'] >= 0.5 else 0
                y_pred.append(pred_label)
                
                predictions.append({
                    'text': text[:60] + "..." if len(text) > 60 else text,
                    'true_label': true_label,
                    'predicted_label': pred_label,
                    'probability': result['ensemble_score'],
                    'correct': pred_label == true_label,
                    'advanced_score': result['advanced_score'],
                    'ml_score': result['ml_score']
                })
                
            except Exception as e:
                print(f"⚠️ Error processing sample {i}: {e}")
                continue
        
        if len(y_true) < 5:
            return {"error": "Insufficient valid samples"}
        
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        try:
            roc_auc = roc_auc_score(y_true, y_prob)
        except ValueError:
            roc_auc = 0.0
        
        # Analyze predictions
        correct_predictions = sum(1 for p in predictions if p['correct'])
        total_predictions = len(predictions)
        
        # False positives and false negatives
        false_positives = [p for p in predictions if p['true_label'] == 0 and p['predicted_label'] == 1]
        false_negatives = [p for p in predictions if p['true_label'] == 1 and p['predicted_label'] == 0]
        
        # Edge case analysis
        edge_cases = [p for p in predictions if 'fraud department' in p['text'].lower() or 'microsoft' in p['text'].lower()]
        edge_accuracy = sum(1 for p in edge_cases if p['correct']) / len(edge_cases) if edge_cases else 0
        
        return {
            "metrics": {
                "accuracy": round(accuracy, 3),
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1_score": round(f1, 3),
                "roc_auc": round(roc_auc, 3)
            },
            "summary": {
                "total_samples": total_predictions,
                "correct_predictions": correct_predictions,
                "false_positives": len(false_positives),
                "false_negatives": len(false_negatives),
                "edge_case_accuracy": round(edge_accuracy, 3)
            },
            "false_positives": false_positives[:3],  # Show first 3
            "false_negatives": false_negatives[:3],  # Show first 3
            "edge_cases": edge_cases,
            "all_predictions": predictions,
            "model_info": {
                "is_trained": self.ensemble_detector.is_trained,
                "method": "logistic_regression" if self.ensemble_detector.is_trained else "weighted_average"
            }
        }
    
    def generate_quick_report(self, results: Dict) -> str:
        """Generate a quick performance report"""
        if "error" in results:
            return f"❌ Evaluation Error: {results['error']}"
        
        metrics = results['metrics']
        summary = results['summary']
        
        report = []
        report.append("=" * 50)
        report.append("QUICK MODEL EVALUATION REPORT")
        report.append("=" * 50)
        
        report.append(f"\n📊 KEY METRICS")
        report.append("-" * 30)
        report.append(f"Accuracy:     {metrics['accuracy']:.3f}")
        report.append(f"Precision:    {metrics['precision']:.3f}")
        report.append(f"Recall:       {metrics['recall']:.3f}")
        report.append(f"F1-Score:     {metrics['f1_score']:.3f}")
        report.append(f"ROC AUC:      {metrics['roc_auc']:.3f}")
        
        report.append(f"\n📈 SUMMARY")
        report.append("-" * 30)
        report.append(f"Total Samples:      {summary['total_samples']}")
        report.append(f"Correct:           {summary['correct_predictions']}")
        report.append(f"False Positives:   {summary['false_positives']}")
        report.append(f"False Negatives:   {summary['false_negatives']}")
        report.append(f"Edge Case Accuracy: {summary['edge_case_accuracy']:.3f}")
        
        report.append(f"\n🔍 MODEL INFO")
        report.append("-" * 30)
        report.append(f"Method:            {results['model_info']['method']}")
        report.append(f"Trained:           {results['model_info']['is_trained']}")
        
        if results['false_positives']:
            report.append(f"\n❌ FALSE POSITIVES (First 3)")
            report.append("-" * 30)
            for fp in results['false_positives']:
                report.append(f"Text: {fp['text']}")
                report.append(f"Prob: {fp['probability']:.3f} (Advanced: {fp['advanced_score']:.3f}, ML: {fp['ml_score']:.3f})")
                report.append("")
        
        if results['false_negatives']:
            report.append(f"\n❌ FALSE NEGATIVES (First 3)")
            report.append("-" * 30)
            for fn in results['false_negatives']:
                report.append(f"Text: {fn['text']}")
                report.append(f"Prob: {fn['probability']:.3f} (Advanced: {fn['advanced_score']:.3f}, ML: {fn['ml_score']:.3f})")
                report.append("")
        
        report.append("=" * 50)
        
        return "\n".join(report)

# Convenience function
def quick_evaluate() -> Dict:
    """Run quick evaluation and return results"""
    evaluator = QuickEvaluator()
    results = evaluator.evaluate_quick()
    report = evaluator.generate_quick_report(results)
    print(report)
    return results
