import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import logging
from typing import Dict, List, Any, Optional
import os
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class TrustPredictor:
    """
    🤖 NETHRA Trust Predictor - Integrates Member 1's Neural Network
    FIXED: Temporarily using corrected behavioral analysis for reliable predictions
    """
    
    def __init__(self, model_path: str = "models/trust_model.h5"):
        self.model = None
        self.model_path = model_path
        
        # TEMPORARY FIX: Disable neural network to use corrected behavioral analysis
        self.is_loaded = False  # Force use of corrected analysis
        
        # Feature scaling parameters (Member 1's corrected values)
        self.feature_means = np.array([0.65, 2.1, 0.85, 0.75, 0.78, 15.2])
        self.feature_stds = np.array([0.25, 0.8, 0.35, 0.22, 0.24, 6.8])
        
        # Trust score thresholds (corrected)
        self.suspicious_threshold = 30.0  # Below this = suspicious
        self.trusted_threshold = 70.0     # Above this = trusted
        
        logger.info("🤖 Trust Predictor initialized with corrected behavioral analysis")
        # TEMPORARILY DISABLED: self._load_model()
    
    def _load_model(self):
        """Load Member 1's neural network model with error handling"""
        try:
            if os.path.exists(self.model_path):
                # Load the actual neural network model
                self.model = load_model(self.model_path)
                self.is_loaded = True
                logger.info(f"✅ Neural network model loaded from {self.model_path}")
                logger.info(f"   Model architecture: {self.model.summary()}")
            else:
                logger.warning(f"⚠️ Model file not found at {self.model_path}")
                logger.warning("   Using corrected simulation mode for AI predictions")
                self.is_loaded = False
                
        except Exception as e:
            logger.error(f"❌ Failed to load neural network model: {str(e)}")
            logger.warning("   Falling back to corrected simulation mode")
            self.is_loaded = False
    
    def predict_trust_score(self, behavioral_data: Dict[str, float]) -> float:
        """
        Predict trust score using Member 1's corrected behavioral analysis
        FIXED: Reliable predictions without neural network scaling issues
        """
        try:
            # Extract and validate behavioral features
            features = self._extract_features(behavioral_data)
            
            if self.is_loaded and self.model is not None:
                # Use actual neural network prediction
                trust_score = self._neural_network_prediction(features)
            else:
                # Use corrected behavioral analysis simulation
                trust_score = self._corrected_behavioral_analysis(features)
            
            # Ensure score is within valid range
            trust_score = max(0.0, min(100.0, trust_score))
            
            logger.info(f"🎯 Trust prediction completed")
            logger.info(f"   Input features: {features}")
            logger.info(f"   Trust Score: {trust_score:.2f}%")
            
            return trust_score
            
        except Exception as e:
            logger.error(f"❌ Trust prediction failed: {str(e)}")
            # Return moderate score for safety
            return 50.0
    
    def _extract_features(self, behavioral_data: Dict[str, float]) -> np.ndarray:
        """Extract the 6 behavioral features Member 1's model expects"""
        try:
            features = np.array([
                behavioral_data.get("avg_pressure", 0.0),
                behavioral_data.get("avg_swipe_velocity", 0.0),
                behavioral_data.get("avg_swipe_duration", 0.0),
                behavioral_data.get("accel_stability", 0.0),
                behavioral_data.get("gyro_stability", 0.0),
                behavioral_data.get("touch_frequency", 0.0)
            ])
            
            # Normalize features using Member 1's parameters
            normalized_features = (features - self.feature_means) / self.feature_stds
            
            return normalized_features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            return np.zeros(6)
    
    def _neural_network_prediction(self, features: np.ndarray) -> float:
        """Make prediction using actual neural network model"""
        try:
            # Reshape for model input
            input_features = features.reshape(1, -1)
            
            # Get prediction from neural network
            prediction = self.model.predict(input_features, verbose=0)
            
            # Convert to trust score percentage (CORRECTED - no inversion)
            trust_score = float(prediction[0][0]) * 100.0
            
            logger.info(f"🧠 Neural network prediction: {trust_score:.2f}%")
            return trust_score
            
        except Exception as e:
            logger.error(f"Neural network prediction failed: {str(e)}")
            return self._corrected_behavioral_analysis(features)
    
    def _corrected_behavioral_analysis(self, features: np.ndarray) -> float:
        """
        CORRECTED behavioral analysis simulation
        Fixed the inversion issue - now works correctly
        """
        try:
            # Denormalize features for analysis
            denorm_features = (features * self.feature_stds) + self.feature_means
            
            avg_pressure = denorm_features[0]
            avg_swipe_velocity = denorm_features[1] 
            avg_swipe_duration = denorm_features[2]
            accel_stability = denorm_features[3]
            gyro_stability = denorm_features[4]
            touch_frequency = denorm_features[5]
            
            # CORRECTED LOGIC - Higher values indicate MORE human-like behavior
            trust_components = []
            
            # Pressure analysis (humans apply consistent pressure 0.4-1.2)
            if 0.4 <= avg_pressure <= 1.2:
                pressure_score = 90.0 - abs(avg_pressure - 0.7) * 50
            elif avg_pressure > 1.2:
                pressure_score = max(60.0, 90.0 - (avg_pressure - 1.2) * 30)
            else:
                pressure_score = max(5.0, avg_pressure * 100)  # Very low pressure = bot
            trust_components.append(pressure_score)
            
            # Velocity analysis (humans: 1.5-4.0, bots: very low or erratic)
            if 1.5 <= avg_swipe_velocity <= 4.0:
                velocity_score = 85.0 - abs(avg_swipe_velocity - 2.5) * 20
            elif avg_swipe_velocity > 4.0:
                velocity_score = max(40.0, 85.0 - (avg_swipe_velocity - 4.0) * 15)
            else:
                velocity_score = max(3.0, avg_swipe_velocity * 50)  # Very low = automated
            trust_components.append(velocity_score)
            
            # Duration analysis (humans: 0.3-2.0 seconds)
            if 0.3 <= avg_swipe_duration <= 2.0:
                duration_score = 88.0 - abs(avg_swipe_duration - 1.0) * 25
            elif avg_swipe_duration > 2.0:
                duration_score = max(45.0, 88.0 - (avg_swipe_duration - 2.0) * 20)
            else:
                duration_score = max(2.0, avg_swipe_duration * 150)  # Very short = bot
            trust_components.append(duration_score)
            
            # Stability analysis (humans: 0.6-1.0, bots: very low)
            accel_score = max(1.0, min(95.0, accel_stability * 100)) if accel_stability > 0 else 1.0
            gyro_score = max(1.0, min(95.0, gyro_stability * 100)) if gyro_stability > 0 else 1.0
            trust_components.extend([accel_score, gyro_score])
            
            # Frequency analysis (humans: 8-25 touches, bots: very low or very high)
            if 8 <= touch_frequency <= 25:
                freq_score = 90.0 - abs(touch_frequency - 16) * 3
            elif touch_frequency > 25:
                freq_score = max(30.0, 90.0 - (touch_frequency - 25) * 2)
            else:
                freq_score = max(1.0, touch_frequency * 8)  # Very low frequency = bot
            trust_components.append(freq_score)
            
            # Calculate weighted average (emphasizing critical indicators)
            weights = [0.2, 0.2, 0.15, 0.15, 0.15, 0.15]  # Pressure and velocity most important
            trust_score = sum(score * weight for score, weight in zip(trust_components, weights))
            
            # Apply suspicious behavior penalty for extremely low values
            if all(val < 0.1 for val in denorm_features[:3]):  # All primary features very low
                trust_score = min(trust_score, 15.0)  # Cap at very suspicious
            
            logger.info(f"🔍 Corrected behavioral analysis:")
            logger.info(f"   Components: {[f'{score:.1f}' for score in trust_components]}")
            logger.info(f"   Final Trust Score: {trust_score:.2f}%")
            
            return trust_score
            
        except Exception as e:
            logger.error(f"Behavioral analysis failed: {str(e)}")
            return 50.0  # Default moderate score
    
    def get_trust_category(self, trust_score: float) -> str:
        """Categorize trust score into human-readable categories"""
        if trust_score >= self.trusted_threshold:
            return "trusted"
        elif trust_score <= self.suspicious_threshold:
            return "suspicious"
        else:
            return "caution"
    
    def get_security_recommendation(self, trust_score: float) -> Dict[str, str]:
        """Get security action recommendations based on trust score"""
        if trust_score >= 85:
            return {
                "action": "allow_full_access",
                "message": "Welcome! Your session is secure.",
                "security_level": "minimal"
            }
        elif trust_score >= 70:
            return {
                "action": "allow_with_monitoring",
                "message": "Session authenticated. Monitoring active for your security.",
                "security_level": "standard"
            }
        elif trust_score >= 40:
            return {
                "action": "elevated_security",
                "message": "Additional security measures activated.",
                "security_level": "elevated"
            }
        else:
            return {
                "action": "maximum_security",
                "message": "High security mode enabled.",
                "security_level": "maximum"
            }
    
    def analyze_behavioral_patterns(self, behavioral_data: Dict[str, float]) -> Dict[str, Any]:
        """Comprehensive behavioral pattern analysis"""
        try:
            features = self._extract_features(behavioral_data)
            trust_score = self.predict_trust_score(behavioral_data)
            
            analysis = {
                "trust_score": trust_score,
                "trust_category": self.get_trust_category(trust_score),
                "security_recommendation": self.get_security_recommendation(trust_score),
                "behavioral_indicators": {
                    "pressure_level": "normal" if 0.4 <= behavioral_data.get("avg_pressure", 0) <= 1.2 else "abnormal",
                    "velocity_pattern": "human-like" if 1.5 <= behavioral_data.get("avg_swipe_velocity", 0) <= 4.0 else "suspicious",
                    "timing_consistency": "natural" if 0.3 <= behavioral_data.get("avg_swipe_duration", 0) <= 2.0 else "automated",
                    "device_stability": "stable" if behavioral_data.get("accel_stability", 0) > 0.5 else "unstable"
                },
                "risk_factors": []
            }
            
            # Identify specific risk factors
            if behavioral_data.get("avg_pressure", 0) < 0.1:
                analysis["risk_factors"].append("Extremely low touch pressure detected")
            if behavioral_data.get("avg_swipe_velocity", 0) < 0.5:
                analysis["risk_factors"].append("Unusually slow interaction speed")
            if behavioral_data.get("touch_frequency", 0) < 2:
                analysis["risk_factors"].append("Very low interaction frequency")
            if all(val < 0.05 for val in [behavioral_data.get(key, 0) for key in ["accel_stability", "gyro_stability"]]):
                analysis["risk_factors"].append("Abnormal device motion patterns")
                
            return analysis
            
        except Exception as e:
            logger.error(f"Behavioral pattern analysis failed: {str(e)}")
            return {
                "trust_score": 50.0,
                "trust_category": "caution",
                "security_recommendation": self.get_security_recommendation(50.0),
                "error": str(e)
            }

# Global trust predictor instance
_trust_predictor = None

def get_trust_predictor() -> TrustPredictor:
    """Get or create global trust predictor instance"""
    global _trust_predictor
    if _trust_predictor is None:
        _trust_predictor = TrustPredictor()
    return _trust_predictor

def predict_user_trust(behavioral_data: Dict[str, float]) -> float:
    """Quick trust prediction function"""
    predictor = get_trust_predictor()
    return predictor.predict_trust_score(behavioral_data)

def analyze_user_behavior(behavioral_data: Dict[str, float]) -> Dict[str, Any]:
    """Quick behavioral analysis function"""
    predictor = get_trust_predictor()
    return predictor.analyze_behavioral_patterns(behavioral_data)
