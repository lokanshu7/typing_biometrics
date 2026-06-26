import pytest
import os
import sys
import asyncio
import time  # <--- Add time import

# Ensure path resolution works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from app.main import app
from app.schemas import EnrollRequest, TypingSession, KeystrokeEvent

def test_root():
    endpoint = None
    for route in app.routes:
        if getattr(route, "path", "") == "/":
            endpoint = route.endpoint
            break
    response = asyncio.run(endpoint())
    assert isinstance(response, dict)
    assert response["message"] == "Typing Biometrics API"

def test_enroll_user():
    # Create a completely unique username for this test run using a timestamp
    unique_user = f"test_user_{int(time.time())}"
    
    keystrokes = [
        KeystrokeEvent(key='t', press_time=100.0, release_time=150.0),
        KeystrokeEvent(key='e', press_time=200.0, release_time=260.0)
    ]
    sessions = [
        TypingSession(
            user_id=unique_user,  # <--- Use unique user
            text='te', 
            keystrokes=keystrokes,
            session_start=0.0, 
            session_end=500.0
        )
    ] * 3
    
    request_data = EnrollRequest(user_id=unique_user, sessions=sessions)  # <--- Use unique user
    
    enroll_endpoint = None
    for route in app.routes:
        if getattr(route, "path", "") == "/enroll_typing":
            enroll_endpoint = route.endpoint
            break
            
    assert enroll_endpoint is not None, "Enroll endpoint path missing"
    
    response = asyncio.run(enroll_endpoint(request_data))
    assert response.decision in ["pass", "fail"]