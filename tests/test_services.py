import pytest
import numpy as np
import os
import sys

# Ensure path resolution works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from app.services import TypingBiometricsService

@pytest.fixture
def service():
    # Return an isolated testing instance
    return TypingBiometricsService()

def test_ensemble_verification_flow(service):
    # Simulate valid tracking keystrokes (minimum 2 keys required)
    keystrokes = [
        {'key': 't', 'press_time': 100.0, 'release_time': 150.0},
        {'key': 'e', 'press_time': 200.0, 'release_time': 260.0}
    ]
    
    # Generate 3 training sessions for a test account
    sessions = [{
        'user_id': 'test_service_user',
        'text': 'te',
        'keystrokes': keystrokes,
        'session_start': 0.0,
        'session_end': 500.0
    }] * 3
    
    # Step 1: Verify enrollment compiles
    enroll_result = service.enroll_user('test_service_user', sessions)
    assert enroll_result["success"] is True
    
    # Step 2: Authenticate using matching parameters
    auth_session = {
        'user_id': 'test_service_user',
        'text': 'te',
        'keystrokes': keystrokes,
        'session_start': 0.0,
        'session_end': 500.0
    }
    
    # Fixed to use the active matching method .authenticate()
    authenticated, confidence = service.authenticate('test_service_user', auth_session)
    assert isinstance(authenticated, bool)
    assert 0.0 <= confidence <= 1.0