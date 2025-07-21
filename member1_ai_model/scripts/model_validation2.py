import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import json
import time
import os
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_curve, auc, classification_report
)
from sklearn.model_selection import cross_val_score
import joblib
import tensorflow as tf

# Set style for better plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class NethraModelValidator:
    """
    Comprehensive validation and performance analysis for NETHRA models
    """
    
    def __init__(self, output_dir='results'):
        self.models = {}
        self.scaler = None
        self.validation_data = {}
        self.results = {}
        self.use_inference_system = False
        self.inference_system = None
        
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Go up one level to nethra_ai/ directory
        project_root = os.path.dirname(script_dir)
        
        # Create results folder in nethra_ai/ directory
        self.output_dir = os.path.join(project_root, output_dir)
        
        # Create output directory with better path handling
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            print(f"Output directory: {self.output_dir}")
        except Exception as e:
            print(f"Could not create directory {self.output_dir}: {e}")
            # Fallback to current directory
            self.output_dir = output_dir
            os.makedirs(self.output_dir, exist_ok=True)
        
        print("NETHRA Model Validation System")
        print("=" * 50)
    
    def load_models(self):
        """Load all available models from any location"""
        print("Loading NETHRA models...")
        
        import glob
        
        # Search for model files anywhere in the project
        model_patterns = {
            'isolation_forest': ['**/*isolation_forest*.pkl', '**/isolation_forest.pkl'],
            'one_class_svm': ['**/*one_class_svm*.pkl', '**/one_class_svm.pkl'],
            'neural_network': ['**/*neural_network*.h5', '**/nethra_neural_network.h5'],
            'scaler': ['**/*scaler*.pkl', '**/scaler.pkl']
        }
        
        models_loaded = 0
        
        for model_name, patterns in model_patterns.items():
            model_found = False
            
            for pattern in patterns:
                files = glob.glob(pattern, recursive=True)
                for file_path in files:
                    if os.path.exists(file_path):
                        print(f"Found {model_name} at: {file_path}")
                        self._load_single_model(model_name, file_path)
                        models_loaded += 1
                        model_found = True
                        break
                if model_found:
                    break
            
            if not model_found:
                print(f"[WARNING] {model_name} not found")
        
        # If no models found, try to use foolproof inference
        if models_loaded == 0:
            print("\n[INFO] No direct model files found. Trying foolproof inference...")
            try:
                from foolproof_inference import FoolproofNethraInference
                
                inference = FoolproofNethraInference()
                if inference.initialize():
                    print("[OK] Using foolproof inference system")
                    self.inference_system = inference
                    self.use_inference_system = True
                    return True
                else:
                    print("[ERROR] Foolproof inference also failed")
                    return False
            except ImportError:
                print("[ERROR] foolproof_inference.py not found")
                return False
        
        self.use_inference_system = False
        print(f"[OK] Loaded {models_loaded} models directly")
        return models_loaded > 0
    
    def _load_single_model(self, model_name, path):
        """Load a single model file"""
        try:
            if model_name == 'scaler':
                self.scaler = joblib.load(path)
                print(f"[OK] Scaler loaded from {path}")
            elif model_name == 'neural_network':
                self.models[model_name] = tf.keras.models.load_model(path)
                print(f"[OK] Neural Network loaded from {path}")
            else:
                self.models[model_name] = joblib.load(path)
                print(f"[OK] {model_name} loaded from {path}")
        except Exception as e:
            print(f"[ERROR] Failed to load {model_name}: {e}")
    
    def generate_test_data(self, n_samples=1000):
        """Generate comprehensive test data for validation"""
        print(f"\nGenerating {n_samples} test samples...")
        
        np.random.seed(42)  # For reproducible results
        
        # Generate normal user data (70% of samples)
        n_normal = int(n_samples * 0.7)
        normal_data = []
        
        for _ in range(n_normal):
            # Realistic normal user patterns
            features = [
                np.random.beta(2, 2) * 0.6 + 0.2,      # avg_pressure (0.2-0.8)
                np.random.normal(160, 30),              # avg_swipe_velocity (100-220)
                np.random.gamma(2, 0.25),               # avg_swipe_duration (0.2-1.0)
                np.random.exponential(0.3),             # accel_stability (0-1.5)
                np.random.exponential(0.1),             # gyro_stability (0-0.5)
                np.random.gamma(2, 1) + 0.5             # touch_frequency (0.5-5.0)
            ]
            normal_data.append(features)
        
        # Generate attacker data (30% of samples)
        n_attack = n_samples - n_normal
        attack_data = []
        
        for _ in range(n_attack):
            # Bot-like attack patterns
            features = [
                np.random.uniform(0.1, 0.4),            # Low, consistent pressure
                np.random.normal(90, 15),               # Slower, consistent swipes
                np.random.normal(0.3, 0.05),            # Very consistent duration
                np.random.uniform(0.01, 0.15),          # Very stable motion
                np.random.uniform(0.005, 0.05),         # Extremely stable gyro
                np.random.uniform(0.2, 1.5)             # Low interaction rate
            ]
            attack_data.append(features)
        
        # Combine data
        X = np.array(normal_data + attack_data)
        y = np.array([1] * n_normal + [0] * n_attack)  # 1=normal, 0=attack
        
        # Shuffle
        indices = np.random.permutation(len(X))
        X = X[indices]
        y = y[indices]
        
        self.validation_data = {'X': X, 'y': y}
        
        print(f"[OK] Generated {len(X)} samples")
        print(f"     Normal users: {np.sum(y == 1)} ({np.mean(y == 1)*100:.1f}%)")
        print(f"     Attackers: {np.sum(y == 0)} ({np.mean(y == 0)*100:.1f}%)")
        
        return X, y
    
    def evaluate_model(self, model_name, model, X, y):
        """Evaluate a single model"""
        print(f"\nEvaluating {model_name}...")
        
        # Handle inference system differently
        if self.use_inference_system and model_name == 'inference_system':
            predictions = []
            prediction_scores = []
            
            print("  Using inference system for predictions...")
            for i, sample in enumerate(X):
                if i % 500 == 0:
                    print(f"    Processing sample {i}/{len(X)}")
                    
                trust_score = self.inference_system.calculate_trust_score(sample.tolist())
                
                # Convert trust score to binary prediction
                pred = 1 if trust_score > 50 else 0
                predictions.append(pred)
                prediction_scores.append(trust_score / 100.0)  # Normalize to 0-1
            
            predictions = np.array(predictions)
            prediction_scores = np.array(prediction_scores)
            
        else:
            # Original model evaluation logic
            # Scale data if scaler available
            if self.scaler is not None:
                X_scaled = self.scaler.transform(X)
            else:
                X_scaled = X
            
            # Get predictions based on model type
            if model_name == 'neural_network':
                predictions_prob = model.predict(X_scaled, verbose=0)
                predictions = (predictions_prob > 0.5).astype(int).flatten()
                prediction_scores = predictions_prob.flatten()
            else:
                # For sklearn models (anomaly detection)
                predictions_raw = model.predict(X_scaled)
                predictions = (predictions_raw == 1).astype(int)  # 1=normal, -1=anomaly -> 1=normal, 0=anomaly
                
                # Get decision scores for ROC curve
                if hasattr(model, 'decision_function'):
                    decision_scores = model.decision_function(X_scaled)
                    # Normalize to 0-1 range
                    prediction_scores = (decision_scores - decision_scores.min()) / (decision_scores.max() - decision_scores.min())
                else:
                    prediction_scores = predictions.astype(float)
        
        # Calculate metrics
        accuracy = accuracy_score(y, predictions)
        precision = precision_score(y, predictions, zero_division=0)
        recall = recall_score(y, predictions, zero_division=0)
        f1 = f1_score(y, predictions, zero_division=0)
        
        # Confusion matrix
        cm = confusion_matrix(y, predictions)
        
        # ROC curve
        try:
            fpr, tpr, _ = roc_curve(y, prediction_scores)
            roc_auc = auc(fpr, tpr)
        except:
            fpr, tpr, roc_auc = None, None, 0
        
        # Store results
        self.results[model_name] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': cm,
            'predictions': predictions,
            'prediction_scores': prediction_scores,
            'fpr': fpr,
            'tpr': tpr,
            'roc_auc': roc_auc
        }
        
        print(f"  Accuracy:  {accuracy:.3f}")
        print(f"  Precision: {precision:.3f}")
        print(f"  Recall:    {recall:.3f}")
        print(f"  F1 Score:  {f1:.3f}")
        print(f"  ROC AUC:   {roc_auc:.3f}")
        
        return self.results[model_name]
    
    def test_inference_speed(self, n_tests=100):
        """Test model inference speed"""
        print(f"\nTesting inference speed ({n_tests} predictions)...")
        
        # Generate test sample
        test_sample = np.random.random((1, 6))
        speed_results = {}
        
        if self.use_inference_system:
            # Test inference system speed
            times = []
            
            for _ in range(n_tests):
                start_time = time.time()
                _ = self.inference_system.calculate_trust_score(test_sample[0].tolist())
                end_time = time.time()
                times.append((end_time - start_time) * 1000)  # Convert to ms
            
            avg_time = np.mean(times)
            std_time = np.std(times)
            
            speed_results['inference_system'] = {
                'avg_time_ms': avg_time,
                'std_time_ms': std_time,
                'min_time_ms': np.min(times),
                'max_time_ms': np.max(times)
            }
            
            print(f"  inference_system: {avg_time:.2f} ± {std_time:.2f} ms")
        
        else:
            # Test individual models
            if self.scaler:
                test_sample_scaled = self.scaler.transform(test_sample)
            else:
                test_sample_scaled = test_sample
            
            for model_name, model in self.models.items():
                times = []
                
                for _ in range(n_tests):
                    start_time = time.time()
                    
                    if model_name == 'neural_network':
                        _ = model.predict(test_sample_scaled, verbose=0)
                    else:
                        _ = model.predict(test_sample_scaled)
                    
                    end_time = time.time()
                    times.append((end_time - start_time) * 1000)  # Convert to ms
                
                avg_time = np.mean(times)
                std_time = np.std(times)
                
                speed_results[model_name] = {
                    'avg_time_ms': avg_time,
                    'std_time_ms': std_time,
                    'min_time_ms': np.min(times),
                    'max_time_ms': np.max(times)
                }
                
                print(f"  {model_name}: {avg_time:.2f} ± {std_time:.2f} ms")
        
        return speed_results
    
    def create_performance_plots(self):
        """Generate comprehensive performance plots"""
        print("\nGenerating performance plots...")
        
        # Set up the plotting
        fig = plt.figure(figsize=(20, 15))
        
        # 1. Model Comparison Bar Chart
        plt.subplot(3, 4, 1)
        models = list(self.results.keys())
        metrics = ['accuracy', 'precision', 'recall', 'f1_score']
        
        x = np.arange(len(models))
        width = 0.2
        
        for i, metric in enumerate(metrics):
            values = [self.results[model][metric] for model in models]
            plt.bar(x + i*width, values, width, label=metric.capitalize())
        
        plt.xlabel('Models')
        plt.ylabel('Score')
        plt.title('Model Performance Comparison')
        plt.xticks(x + width*1.5, models, rotation=45)
        plt.legend()
        plt.ylim(0, 1)
        
        # 2. ROC Curves
        plt.subplot(3, 4, 2)
        for model_name in self.results:
            if self.results[model_name]['fpr'] is not None:
                plt.plot(
                    self.results[model_name]['fpr'], 
                    self.results[model_name]['tpr'],
                    label=f"{model_name} (AUC = {self.results[model_name]['roc_auc']:.3f})"
                )
        
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curves')
        plt.legend()
        plt.grid(True)
        
        # 3-6. Confusion Matrices
        for i, model_name in enumerate(self.results):
            plt.subplot(3, 4, 3 + i)
            cm = self.results[model_name]['confusion_matrix']
            
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                       xticklabels=['Attack', 'Normal'],
                       yticklabels=['Attack', 'Normal'])
            plt.title(f'Confusion Matrix\n{model_name}')
            plt.ylabel('True Label')
            plt.xlabel('Predicted Label')
        
        # 7. Trust Score Distribution
        plt.subplot(3, 4, 7)
        X, y = self.validation_data['X'], self.validation_data['y']
        
        # Use best model for trust score calculation
        best_model_name = max(self.results.keys(), key=lambda x: self.results[x]['f1_score'])
        trust_scores = self._calculate_trust_scores(X, best_model_name)
        
        normal_scores = trust_scores[y == 1]
        attack_scores = trust_scores[y == 0]
        
        plt.hist(normal_scores, bins=30, alpha=0.7, label='Normal Users', color='green')
        plt.hist(attack_scores, bins=30, alpha=0.7, label='Attackers', color='red')
        plt.axvline(x=40, color='orange', linestyle='--', label='Mirage Trigger (40)')
        plt.xlabel('Trust Score')
        plt.ylabel('Frequency')
        plt.title('Trust Score Distribution')
        plt.legend()
        
        # 8. Feature Importance (if available)
        plt.subplot(3, 4, 8)
        feature_names = [
            'Avg Pressure', 'Swipe Velocity', 'Swipe Duration',
            'Accel Stability', 'Gyro Stability', 'Touch Frequency'
        ]
        
        # Calculate feature importance using correlation with labels
        feature_importance = []
        for i in range(6):
            corr = np.corrcoef(X[:, i], y)[0, 1]
            feature_importance.append(abs(corr))
        
        plt.barh(feature_names, feature_importance)
        plt.xlabel('Feature Importance (|Correlation|)')
        plt.title('Feature Importance Analysis')
        
        # 9. Prediction Confidence
        plt.subplot(3, 4, 9)
        for model_name in self.results:
            scores = self.results[model_name]['prediction_scores']
            plt.hist(scores, bins=20, alpha=0.6, label=model_name)
        
        plt.xlabel('Prediction Confidence')
        plt.ylabel('Frequency')
        plt.title('Prediction Confidence Distribution')
        plt.legend()
        
        # 10. Error Analysis
        plt.subplot(3, 4, 10)
        error_data = []
        
        for model_name in self.results:
            predictions = self.results[model_name]['predictions']
            errors = y != predictions
            
            false_positives = np.sum((y == 0) & (predictions == 1))  # Attack classified as normal
            false_negatives = np.sum((y == 1) & (predictions == 0))  # Normal classified as attack
            
            error_data.append([false_positives, false_negatives])
        
        error_df = pd.DataFrame(error_data, 
                               columns=['False Positives', 'False Negatives'],
                               index=list(self.results.keys()))
        
        error_df.plot(kind='bar', ax=plt.gca())
        plt.title('Error Analysis')
        plt.ylabel('Number of Errors')
        plt.xticks(rotation=45)
        plt.legend()
        
        # 11. Performance vs Speed Trade-off
        plt.subplot(3, 4, 11)
        if hasattr(self, 'speed_results'):
            f1_scores = [self.results[model]['f1_score'] for model in self.results]
            avg_times = [self.speed_results[model]['avg_time_ms'] for model in self.results]
            
            plt.scatter(avg_times, f1_scores, s=100)
            
            for i, model in enumerate(self.results):
                plt.annotate(model, (avg_times[i], f1_scores[i]), 
                           xytext=(5, 5), textcoords='offset points')
            
            plt.xlabel('Average Inference Time (ms)')
            plt.ylabel('F1 Score')
            plt.title('Performance vs Speed Trade-off')
            plt.grid(True)
        
        # 12. Real-time Performance Simulation
        plt.subplot(3, 4, 12)
        
        # Simulate real-time trust scores over time
        time_points = range(100)
        simulated_scores = []
        
        for t in time_points:
            # Simulate gradually changing behavior
            noise = np.sin(t/10) * 10 + np.random.normal(0, 5)
            base_score = 70 + noise
            simulated_scores.append(max(0, min(100, base_score)))
        
        plt.plot(time_points, simulated_scores, 'b-', linewidth=2, label='Trust Score')
        plt.axhline(y=40, color='red', linestyle='--', label='Mirage Trigger')
        plt.axhline(y=70, color='green', linestyle='--', label='Trusted Threshold')
        plt.fill_between(time_points, 0, 40, alpha=0.3, color='red', label='Suspicious Zone')
        plt.fill_between(time_points, 40, 70, alpha=0.3, color='orange', label='Caution Zone')
        plt.fill_between(time_points, 70, 100, alpha=0.3, color='green', label='Trusted Zone')
        
        plt.xlabel('Time (seconds)')
        plt.ylabel('Trust Score')
        plt.title('Real-time Trust Score Simulation')
        plt.legend()
        plt.ylim(0, 100)
        
        # Save plot
        plot_path = os.path.join(self.output_dir, 'nethra_performance_analysis.png')
        
        # Ensure directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        try:
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            print(f"[OK] Performance plots saved to {plot_path}")
        except Exception as e:
            print(f"[ERROR] Could not save plots: {e}")
            print(f"Attempted path: {plot_path}")
        
        return plot_path
    
    def _calculate_trust_scores(self, X, model_name):
        """Calculate trust scores (0-100) for visualization"""
        
        if self.use_inference_system:
            trust_scores = []
            for sample in X:
                score = self.inference_system.calculate_trust_score(sample.tolist())
                trust_scores.append(score)
            return np.array(trust_scores)
        
        model = self.models[model_name]
        
        if self.scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        if model_name == 'neural_network':
            scores = model.predict(X_scaled, verbose=0).flatten()
            trust_scores = scores * 100
        else:
            predictions = model.predict(X_scaled)
            # Convert -1/1 to 0-100 scale
            trust_scores = np.where(predictions == 1, 85, 25)
            
            # Add some variance for visualization
            trust_scores = trust_scores + np.random.normal(0, 5, len(trust_scores))
        
        return np.clip(trust_scores, 0, 100)
    
    def generate_detailed_report(self):
        """Generate detailed validation report"""
        print("\nGenerating detailed validation report...")
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'validation_summary': {
                'total_models_tested': len(self.results),
                'test_samples': len(self.validation_data['X']),
                'normal_samples': int(np.sum(self.validation_data['y'] == 1)),
                'attack_samples': int(np.sum(self.validation_data['y'] == 0))
            },
            'model_performance': {},
            'recommendations': [],
            'security_analysis': {}
        }
        
        # Best model identification
        best_model = max(self.results.keys(), key=lambda x: self.results[x]['f1_score'])
        
        for model_name, results in self.results.items():
            report['model_performance'][model_name] = {
                'accuracy': float(results['accuracy']),
                'precision': float(results['precision']),
                'recall': float(results['recall']),
                'f1_score': float(results['f1_score']),
                'roc_auc': float(results['roc_auc']) if results['roc_auc'] else 0,
                'is_best_model': model_name == best_model
            }
        
        # Security analysis
        best_results = self.results[best_model]
        false_positives = np.sum((self.validation_data['y'] == 0) & (best_results['predictions'] == 1))
        false_negatives = np.sum((self.validation_data['y'] == 1) & (best_results['predictions'] == 0))
        
        attack_samples = np.sum(self.validation_data['y'] == 0)
        normal_samples = np.sum(self.validation_data['y'] == 1)
        
        report['security_analysis'] = {
            'missed_attacks': int(false_positives),
            'false_alarms': int(false_negatives),
            'attack_detection_rate': float((attack_samples - false_positives) / attack_samples),
            'false_alarm_rate': float(false_negatives / normal_samples),
            'recommended_threshold': 40
        }
        
        # Recommendations
        if report['security_analysis']['attack_detection_rate'] > 0.9:
            report['recommendations'].append("Excellent attack detection capability")
        elif report['security_analysis']['attack_detection_rate'] > 0.8:
            report['recommendations'].append("Good attack detection, consider fine-tuning")
        else:
            report['recommendations'].append("Attack detection needs improvement")
        
        if report['security_analysis']['false_alarm_rate'] < 0.1:
            report['recommendations'].append("Low false alarm rate - good user experience")
        else:
            report['recommendations'].append("Consider adjusting threshold to reduce false alarms")
        
        # Save report
        report_path = os.path.join(self.output_dir, 'validation_report.json')
        
        # Ensure directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        try:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"[OK] Detailed report saved to {report_path}")
        except Exception as e:
            print(f"[ERROR] Could not save report: {e}")
            print(f"Attempted path: {report_path}")
            return report
        
        # Print summary
        print("\n" + "=" * 60)
        print("NETHRA MODEL VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Best Model: {best_model}")
        print(f"Overall Accuracy: {best_results['accuracy']:.1%}")
        print(f"Attack Detection Rate: {report['security_analysis']['attack_detection_rate']:.1%}")
        print(f"False Alarm Rate: {report['security_analysis']['false_alarm_rate']:.1%}")
        print(f"F1 Score: {best_results['f1_score']:.3f}")
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        
        return report
    
    def run_complete_validation(self):
        """Run complete validation pipeline"""
        print("Starting Complete NETHRA Model Validation")
        print("=" * 60)
        
        # Step 1: Load models
        if not self.load_models():
            print("[ERROR] No models found for validation")
            return False
        
        # Step 2: Generate test data
        X, y = self.generate_test_data(n_samples=2000)
        
        # Step 3: Evaluate each model
        if self.use_inference_system:
            # Evaluate the inference system as a single model
            self.evaluate_model('inference_system', None, X, y)
        else:
            # Evaluate each individual model
            for model_name, model in self.models.items():
                self.evaluate_model(model_name, model, X, y)
        
        # Step 4: Test inference speed
        self.speed_results = self.test_inference_speed()
        
        # Step 5: Create performance plots
        self.create_performance_plots()
        
        # Step 6: Generate detailed report
        report = self.generate_detailed_report()
        
        print(f"\n[SUCCESS] Validation complete!")
        print(f"Results saved in: {self.output_dir}/")
        print("Files created:")
        print("  - nethra_performance_analysis.png (plots)")
        print("  - validation_report.json (detailed metrics)")
        
        return True

def main():
    """Main validation function with custom directory naming"""
    from datetime import datetime
    
    # Create date-based directory name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    custom_output_dir = f'validation_{timestamp}'
    
    validator = NethraModelValidator(output_dir=custom_output_dir)
    
    if validator.run_complete_validation():
        print(f"\n🎉 NETHRA models validated successfully!")
        print(f"Check the {custom_output_dir}/ folder for detailed analysis.")
    else:
        print(f"\n❌ Validation failed - check your model files")

if __name__ == "__main__":
    main()