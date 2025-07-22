from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List
from datetime import datetime

class BehavioralFeatures(BaseModel):
    """Member 1's 6 behavioral features"""
    avg_pressure: float = Field(..., ge=0.0, description="Average touch pressure")
    avg_swipe_velocity: float = Field(..., ge=0.0, description="Average swipe velocity") 
    avg_swipe_duration: float = Field(..., ge=0.0, description="Average swipe duration")
    accel_stability: float = Field(..., ge=0.0, description="Accelerometer stability")
    gyro_stability: float = Field(..., ge=0.0, description="Gyroscope stability")
    touch_frequency: float = Field(..., ge=0.0, description="Touch frequency")

class TrustPredictionRequest(BaseModel):
    user_id: int
    session_id: Optional[int] = None
    behavioral_features: BehavioralFeatures
    timestamp: Optional[str] = None
    device_info: Optional[Dict] = None

class TrustPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    success: bool
    trust_score: float = Field(..., ge=0.0, le=100.0)
    trust_category: str
    personal_threshold: float
    is_below_threshold: bool
    mirage_activated: bool
    mirage_intensity: Optional[str] = None
    security_action: str
    user_message: str
    session_count: int
    learning_phase: bool

class ThresholdAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    status: str
    current_threshold: float
    is_learning_phase: bool
    sessions_completed: int
    sessions_needed: int
    average_trust_score: Optional[float] = None
    score_history: Optional[List[float]] = None
