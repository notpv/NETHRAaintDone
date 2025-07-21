import numpy as np
import tensorflow as tf
import joblib
import json
import os

class NeuralTrustAnalyzer:
    """
    Pure Neural Network Trust Score Calculator
    ONLY calculates trust scores - nothing else
    """
    
    def __init__(self, model_dir='model'):
        self.model = None
        self.scaler = None
        self.model_dir = model_dir
        self.is_initialized = False
        
    def initialize(self):
        """Load neural network and scaler"""
        print("Loading NETHRA Neural Network...")
        
        model_path = os.path.join(self.model_dir, 'nethra_neural_network.h5')
        scaler_path = os.path.join(self.model_dir, 'nethra_scaler.pkl')
        
        try:
            # Load model
            self.model = tf.keras.models.load_model(model_path)
            print("✓ Neural network loaded")
            
            # Load scaler  
            self.scaler = joblib.load(scaler_path)
            print("✓ Scaler loaded")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"✗ Failed to load model: {e}")
            return False
    
    def calculate_trust_score(self, behavioral_features):
        """
        Calculate trust score from behavioral features
        
        Input: List of 6 features [avg_pressure, avg_swipe_velocity, avg_swipe_duration, 
                                  accel_stability, gyro_stability, touch_frequency]
        Output: Trust score (0-100)
        """
        if not self.is_initialized:
            if not self.initialize():
                return 50  # Default neutral score
        
        try:
            # Ensure we have 6 features
            if len(behavioral_features) != 6:
                print(f"Warning: Expected 6 features, got {len(behavioral_features)}")
                return 50
            
            # Convert to numpy array
            features = np.array(behavioral_features).reshape(1, -1)
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Get prediction (0.0 - 1.0)
            prediction = self.model.predict(features_scaled, verbose=0)[0][0]
            
            # Convert to trust score (0-100)
            trust_score = int(prediction * 100)
            
            return max(0, min(100, trust_score))
            
        except Exception as e:
            print(f"Error calculating trust score: {e}")
            return 50  # Fallback score
    
    def analyze_user_sessions(self, user_sessions):
        """
        Analyze multiple user sessions (for Member 2's SQLite integration)
        
        Input: List of session data dictionaries
        Output: Average trust score
        """
        if not user_sessions:
            return 50  # New user default
        
        trust_scores = []
        
        for session in user_sessions:
            # Extract features from session data
            features = [
                session.get('avg_pressure', 0.5),
                session.get('avg_swipe_velocity', 150.0),
                session.get('avg_swipe_duration', 0.5),
                session.get('accel_stability', 0.3),
                session.get('gyro_stability', 0.1),
                session.get('touch_frequency', 2.0)
            ]
            
            score = self.calculate_trust_score(features)
            trust_scores.append(score)
        
        # Return weighted average (recent sessions matter more)
        if len(trust_scores) <= 3:
            return np.mean(trust_scores)
        else:
            # Weight recent sessions more heavily
            weights = np.exp(np.linspace(0, 1, len(trust_scores)))
            return np.average(trust_scores, weights=weights)

# Simple usage for Member 2
def get_trust_score(behavioral_features):
    """
    Simple function for Member 2 to call
    Input: [avg_pressure, avg_swipe_velocity, avg_swipe_duration, 
            accel_stability, gyro_stability, touch_frequency]
    Output: Trust score 0-100
    """
    analyzer = NeuralTrustAnalyzer()
    return analyzer.calculate_trust_score(behavioral_features)

def get_user_trust_score(user_sessions):
    """
    Function for Member 2's SQLite integration
    Input: List of user session data
    Output: Trust score 0-100
    """
    analyzer = NeuralTrustAnalyzer()
    return analyzer.analyze_user_sessions(user_sessions)

# Test the system
def test_neural_inference():
    """Test neural network inference"""
    print("Testing Neural Network Inference")
    print("=" * 35)
    
    analyzer = NeuralTrustAnalyzer()
    
    if analyzer.initialize():
        test_cases = [
            {
                "name": "Normal User",
                "features": [0.6, 150, 0.5, 0.3, 0.1, 2.0]
            },
            {
                "name": "Suspicious User",
                "features": [0.2, 80, 0.3, 0.05, 0.02, 0.5]  
            },
            {
                "name": "High Trust User",
                "features": [0.7, 180, 0.6, 0.4, 0.15, 2.5]
            }
        ]
        
        for test in test_cases:
            score = analyzer.calculate_trust_score(test["features"])
            
            if score > 70:
                status = "TRUSTED"
            elif score > 40:
                status = "CAUTION"
            else:
                status = "SUSPICIOUS - TRIGGER MIRAGE"
            
            print(f"{test['name']}: {score} - {status}")
        
        return True
    else:
        print("Failed to initialize neural network")
        return False

if __name__ == "__main__":
    test_neural_inference()