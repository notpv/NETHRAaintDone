import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import statistics
import logging

logger = logging.getLogger(__name__)

class BehavioralAnalyzer:
    """
    Analyzer for behavioral patterns and anomaly detection
    Works with Member 1's AI model features
    """
    
    def __init__(self):
        # Member 1's feature names
        self.feature_names = [
            'avg_pressure',
            'avg_swipe_velocity', 
            'avg_swipe_duration',
            'accel_stability',
            'gyro_stability',
            'touch_frequency'
        ]
        
        # Feature ranges for anomaly detection
        self.normal_ranges = {
            'avg_pressure': (0.1, 2.0),
            'avg_swipe_velocity': (0.5, 10.0),
            'avg_swipe_duration': (0.1, 3.0),
            'accel_stability': (0.0, 1.0),
            'gyro_stability': (0.0, 1.0),
            'touch_frequency': (0.1, 20.0)
        }
    
    def validate_behavioral_features(self, features: Dict) -> Tuple[bool, List[str]]:
        """Validate behavioral features for anomalies"""
        issues = []
        
        for feature_name, (min_val, max_val) in self.normal_ranges.items():
            if feature_name in features:
                value = features[feature_name]
                
                if not isinstance(value, (int, float)):
                    issues.append(f"{feature_name}: Invalid data type")
                elif value < min_val or value > max_val:
                    issues.append(f"{feature_name}: Value {value} outside normal range [{min_val}, {max_val}]")
                elif np.isnan(value) or np.isinf(value):
                    issues.append(f"{feature_name}: Invalid numeric value")
            else:
                issues.append(f"Missing feature: {feature_name}")
        
        return len(issues) == 0, issues
    
    def calculate_feature_stability(self, feature_history: List[Dict]) -> Dict:
        """Calculate stability metrics for behavioral features"""
        if len(feature_history) < 2:
            return {"stability": "insufficient_data"}
        
        stability_metrics = {}
        
        for feature_name in self.feature_names:
            values = []
            for record in feature_history:
                if feature_name in record:
                    values.append(record[feature_name])
            
            if len(values) >= 2:
                mean_val = statistics.mean(values)
                std_val = statistics.stdev(values) if len(values) > 1 else 0
                coefficient_of_variation = std_val / mean_val if mean_val != 0 else 0
                
                # Stability classification
                if coefficient_of_variation < 0.1:
                    stability = "very_stable"
                elif coefficient_of_variation < 0.2:
                    stability = "stable"
                elif coefficient_of_variation < 0.4:
                    stability = "moderate"
                else:
                    stability = "unstable"
                
                stability_metrics[feature_name] = {
                    "mean": round(mean_val, 4),
                    "std_dev": round(std_val, 4),
                    "coefficient_of_variation": round(coefficient_of_variation, 4),
                    "stability": stability,
                    "samples": len(values)
                }
        
        return stability_metrics
    
    def detect_behavioral_shift(self, recent_features: Dict, baseline_features: Dict, threshold: float = 0.3) -> Dict:
        """Detect significant shifts in behavioral patterns"""
        shifts_detected = {}
        
        for feature_name in self.feature_names:
            if feature_name in recent_features and feature_name in baseline_features:
                recent_val = recent_features[feature_name]
                baseline_val = baseline_features[feature_name]
                
                if baseline_val != 0:
                    relative_change = abs(recent_val - baseline_val) / baseline_val
                    
                    if relative_change > threshold:
                        shifts_detected[feature_name] = {
                            "baseline_value": baseline_val,
                            "recent_value": recent_val,
                            "relative_change": round(relative_change, 4),
                            "severity": "high" if relative_change > 0.5 else "moderate"
                        }
        
        return {
            "shifts_detected": len(shifts_detected) > 0,
            "total_shifts": len(shifts_detected),
            "feature_shifts": shifts_detected,
            "overall_severity": "high" if any(
                shift["severity"] == "high" for shift in shifts_detected.values()
            ) else "moderate" if shifts_detected else "none"
        }
    
    def analyze_session_patterns(self, session_data: List[Dict]) -> Dict:
        """Analyze patterns within a session"""
        if not session_data:
            return {"error": "No session data provided"}
        
        # Calculate session statistics
        session_length = len(session_data)
        
        # Feature trends
        trends = {}
        for feature_name in self.feature_names:
            values = [record.get(feature_name, 0) for record in session_data]
            
            if len(values) > 1:
                # Simple trend detection
                            # Simple trend detection
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]
                
                if first_half and second_half:
                    first_avg = statistics.mean(first_half)
                    second_avg = statistics.mean(second_half)
                    trend_direction = "increasing" if second_avg > first_avg else "decreasing"
                    trend_magnitude = abs(second_avg - first_avg) / first_avg if first_avg != 0 else 0
                    
                    trends[feature_name] = {
                        "direction": trend_direction,
                        "magnitude": round(trend_magnitude, 4),
                        "significance": "high" if trend_magnitude > 0.2 else "low"
                    }
        
        return {
            "session_length": session_length,
            "feature_trends": trends,
            "timestamp": datetime.utcnow().isoformat()
        }

# Global analyzer instance
_behavioral_analyzer = None

def get_behavioral_analyzer() -> BehavioralAnalyzer:
    """Get or create global behavioral analyzer instance"""
    global _behavioral_analyzer
    if _behavioral_analyzer is None:
        _behavioral_analyzer = BehavioralAnalyzer()
    return _behavioral_analyzer

