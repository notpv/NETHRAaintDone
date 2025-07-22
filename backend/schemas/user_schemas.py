from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool
    session_count: Optional[int] = 0
    average_trust_score: Optional[float] = 50.0
    personal_threshold: Optional[float] = 40.0
    is_learning_phase: Optional[bool] = True

class BehavioralBaselineResponse(BaseModel):
    avg_pressure_baseline: float
    avg_swipe_velocity_baseline: float
    avg_swipe_duration_baseline: float
    accel_stability_baseline: float
    gyro_stability_baseline: float
    touch_frequency_baseline: float
    established_sessions: int
    is_baseline_ready: bool
