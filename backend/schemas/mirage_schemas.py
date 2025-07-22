from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class MirageActivationRequest(BaseModel):
    user_id: int
    trust_score: float = Field(..., ge=0.0, le=100.0)
    session_id: Optional[int] = None

class MirageConfigResponse(BaseModel):
    intensity_level: str
    fake_balance: float
    network_delay_seconds: int
    fake_error_probability: float
    show_fake_transactions: bool
    enable_cognitive_challenges: bool
    mirage_duration_minutes: int

class FakeTransactionResponse(BaseModel):
    id: str
    type: str
    amount: float
    direction: str
    timestamp: str
    description: str
    balance_after: float

class MirageStatusResponse(BaseModel):
    mirage_active: bool
    user_id: int
    activated_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    trust_score_trigger: Optional[float] = None
    intensity_level: Optional[str] = None
    interactions_count: Optional[int] = None
    fake_transactions_shown: Optional[int] = None
