from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class KeystrokeEvent(BaseModel):
    """Single keystroke event with timing"""
    key: str
    press_time: float
    release_time: float
    
    @property
    def dwell_time(self) -> float:
        return self.release_time - self.press_time

class TypingSession(BaseModel):
    """Complete typing session data"""
    user_id: str
    text: str
    keystrokes: List[KeystrokeEvent]
    session_start: float
    session_end: float

class EnrollRequest(BaseModel):
    """Request to enroll a new user"""
    user_id: str = Field(..., min_length=3, max_length=50)
    sessions: List[TypingSession] = Field(..., min_items=3, max_items=10)

class AuthenticateRequest(BaseModel):
    """Request to authenticate a user"""
    user_id: str
    session: TypingSession

# Standardized response format
class ActivityEvent(BaseModel):
    """Activity logging event"""
    event_id: str
    user_id: str
    module: str = "typing_biometrics"
    action: str
    purpose: str = "learning_demo"
    result: str
    score: Optional[float] = None
    timestamp: str

class StandardResponse(BaseModel):
    """Standard API response format"""
    module: str = "typing_biometrics"
    score: Optional[float] = None
    decision: str  # pass | fail | inconclusive
    confidence: float
    metadata: Dict[str, Any] = {}
    activity_event: ActivityEvent
    latency_ms: int

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    module: str
    version: str

class VersionResponse(BaseModel):
    """Version metadata response"""
    module: str
    version: str
    model_name: str
    model_version: str
    features: List[str]
    description: str
