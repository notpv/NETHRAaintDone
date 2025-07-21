import numpy as np
import json
import os
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

class NeuralNetworkTrainer:
    """
    Neural Network Only - Clean and Simple
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Create directories
        os.makedirs('model', exist_ok=True)
        
    def generate_training_data(self, n_samples=3000):
        """Generate behavioral training data"""
        print(f"Generating {n_samples} training samples...")
        
        np.random.seed(42)
        
        # Normal users (70%)
        n_normal = int(n_samples * 0.7)
        normal_data = []
        
        for _ in range(n_normal):
            features = [
                np.random.beta(2, 2) * 0.6 + 0.2,      # avg_pressure (0.2-0.8)
                np.random.normal(160, 30),              # avg_swipe_velocity 
                np.random.gamma(2, 0.25),               # avg_swipe_duration
                np.random.exponential(0.3),             # accel_stability
                np.random.exponential(0.1),             # gyro_stability
                np.random.gamma(2, 1) + 0.5             # touch_frequency
            ]
            normal_data.append(features)
        
        # Attackers (30%)
        n_attack = n_samples - n_normal
        attack_data = []
        
        for _ in range(n_attack):
            features = [
                np.random.uniform(0.1, 0.4),            # Low pressure
                np.random.normal(90, 15),               # Slow swipes
                np.random.normal(0.3, 0.05),            # Consistent duration
                np.random.uniform(0.01, 0.15),          # Very stable
                np.random.uniform(0.005, 0.05),         # Extremely stable
                np.random.uniform(0.2, 1.5)             # Low interaction
            ]
            attack_data.append(features)
        
        # Combine and shuffle
        X = np.array(normal_data + attack_data)
        y = np.array([1] * n_normal + [0] * n_attack)  # 1=normal, 0=attack
        
        indices = np.random.permutation(len(X))
        X, y = X[indices], y[indices]
        
        print(f"Generated {len(X)} samples: {np.sum(y==1)} normal, {np.sum(y==0)} attacks")
        return X, y
    
    def build_model(self, input_features=6):
        """Build neural network model"""
        print("Building neural network...")
        
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(input_features,)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')  # 0-1 output
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, X, y):
        """Train the neural network"""
        print("Training neural network...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Build model
        self.model = self.build_model()
        
        # Train with early stopping
        history = self.model.fit(
            X_train_scaled, y_train,
            validation_data=(X_test_scaled, y_test),
            epochs=50,
            batch_size=32,
            verbose=1,
            callbacks=[
                tf.keras.callbacks.EarlyStopping(
                    patience=10, 
                    restore_best_weights=True
                )
            ]
        )
        
        # Evaluate
        predictions = self.model.predict(X_test_scaled, verbose=0)
        predictions_binary = (predictions > 0.5).astype(int).flatten()
        
        accuracy = accuracy_score(y_test, predictions_binary)
        precision = precision_score(y_test, predictions_binary)
        recall = recall_score(y_test, predictions_binary)
        f1 = f1_score(y_test, predictions_binary)
        
        print(f"\nTraining Results:")
        print(f"Accuracy:  {accuracy:.3f}")
        print(f"Precision: {precision:.3f}")
        print(f"Recall:    {recall:.3f}")
        print(f"F1 Score:  {f1:.3f}")
        
        self.is_trained = True
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
    
    def save_model(self):
        """Save model and scaler for Member 2"""
        print("Saving model for Member 2...")
        
        # Save neural network
        self.model.save('model/nethra_neural_network.h5')
        print("✓ Saved: model/nethra_neural_network.h5")
        
        # Save scaler
        joblib.dump(self.scaler, 'model/nethra_scaler.pkl')
        print("✓ Saved: model/nethra_scaler.pkl")
        
        # Save model info for Member 2
        model_info = {
            "model_type": "TensorFlow/Keras Neural Network",
            "model_file": "nethra_neural_network.h5",
            "scaler_file": "nethra_scaler.pkl",
            "input_features": 6,
            "feature_names": [
                "avg_pressure",      # 0: Touch pressure (0.0-1.0)
                "avg_swipe_velocity", # 1: Swipe speed (pixels/sec)
                "avg_swipe_duration", # 2: Swipe duration (seconds)
                "accel_stability",    # 3: Accelerometer variance
                "gyro_stability",     # 4: Gyroscope variance
                "touch_frequency"     # 5: Touches per second
            ],
            "output": "Trust probability (0.0-1.0)",
            "usage": "multiply output by 100 to get trust score 0-100",
            "threshold_recommendations": {
                "mirage_trigger": "< 0.4 (40% trust)",
                "caution_zone": "0.4 - 0.7 (40-70% trust)",
                "trusted_zone": "> 0.7 (70%+ trust)"
            }
        }
        
        with open('model/model_info.json', 'w') as f:
            json.dump(model_info, f, indent=2)
        print("✓ Saved: model/model_info.json")
        
        print("\n🎯 MODEL READY FOR MEMBER 2!")
        print("Send her the entire 'model/' folder")
    
    def test_inference(self):
        """Test the saved model"""
        print("\nTesting inference...")
        
        # Load saved model
        loaded_model = tf.keras.models.load_model('model/nethra_neural_network.h5')
        loaded_scaler = joblib.load('model/nethra_scaler.pkl')
        
        # Test samples
        test_cases = [
            {
                "name": "Normal User",
                "features": [0.6, 150, 0.5, 0.3, 0.1, 2.0]
            },
            {
                "name": "Suspicious User", 
                "features": [0.2, 80, 0.3, 0.05, 0.02, 0.5]
            }
        ]
        
        for test in test_cases:
            features = np.array(test["features"]).reshape(1, -1)
            features_scaled = loaded_scaler.transform(features)
            
            prediction = loaded_model.predict(features_scaled, verbose=0)[0][0]
            trust_score = int(prediction * 100)
            
            print(f"{test['name']}: Trust Score = {trust_score}")
    
    def run_complete_training(self):
        """Complete training pipeline"""
        print("NETHRA Neural Network Training")
        print("=" * 40)
        
        # Generate data
        X, y = self.generate_training_data()
        
        # Train model
        results = self.train(X, y)
        
        # Save model
        self.save_model()
        
        # Test inference
        self.test_inference()
        
        print(f"\n✅ TRAINING COMPLETE!")
        print(f"F1 Score: {results['f1_score']:.3f}")
        return True

def main():
    trainer = NeuralNetworkTrainer()
    trainer.run_complete_training()

if __name__ == "__main__":
    main()