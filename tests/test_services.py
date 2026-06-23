import pytest
import os
import sys
import shutil
import numpy as np


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from services import TypingBiometricsService, DATA_PATH, LOG_PATH

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Fixture to clear out existing data before and after runs so tests stay clean."""
    if os.path.exists("data"):
        shutil.rmtree("data")
    yield
    if os.path.exists("data"):
        shutil.rmtree("data")

@pytest.fixture
def mock_enrollment_sessions():
    """Generates 3 separate typing sessions with slight human-like timing variations."""
    return [
        {
            "keystrokes": [
                {"key": "u", "press_time": 100, "release_time": 180},
                {"key": "n", "press_time": 250, "release_time": 320},
                {"key": "n", "press_time": 400, "release_time": 470},
                {"key": "a", "press_time": 550, "release_time": 610},
                {"key": "t", "press_time": 700, "release_time": 780}
            ]
        },
        {
            # Session 2: Slightly faster typing variant
            "keystrokes": [
                {"key": "u", "press_time": 95, "release_time": 170},
                {"key": "n", "press_time": 240, "release_time": 310},
                {"key": "n", "press_time": 390, "release_time": 460},
                {"key": "a", "press_time": 530, "release_time": 595},
                {"key": "t", "press_time": 680, "release_time": 750}
            ]
        },
        {
            "keystrokes": [
                {"key": "u", "press_time": 105, "release_time": 190},
                {"key": "n", "press_time": 265, "release_time": 335},
                {"key": "n", "press_time": 415, "release_time": 485},
                {"key": "a", "press_time": 570, "release_time": 630},
                {"key": "t", "press_time": 720, "release_time": 800}
            ]
        }
    ]
    # Returning 3 sessions as required by Isolation Forest validation limit
    return [single_session, single_session, single_session]

def test_feature_extraction_dimensions(mock_enrollment_sessions):
    service = TypingBiometricsService()
    ks = mock_enrollment_sessions[0]["keystrokes"]
    features = service.extract_features(ks)
    
    assert features.size == 24, f"Expected 24 extraction metrics, but got {features.size}"

def test_successful_enrollment_and_persistence(mock_enrollment_sessions):
    service = TypingBiometricsService()
    
    # Run the user enrollment process
    response = service.enroll_user(user_id="user_001", sessions=mock_enrollment_sessions)
    assert response["success"] is True
    
    # 1. Verify file persistence actually created the pickle file on disk
    assert os.path.exists(DATA_PATH) is True
    
    # 2. Verify server-restart simulation reads from disk 
    new_service_instance = TypingBiometricsService()
    assert "user_001" in new_service_instance.user_profiles

def test_ensemble_verification_flow(mock_enrollment_sessions):
    service = TypingBiometricsService()
    service.enroll_user(user_id="user_001", sessions=mock_enrollment_sessions)
    
    # Grab a fresh typing sample to verify against the saved profile
    test_session = mock_enrollment_sessions[0]
    
    # Execute the verified endpoint call method
    authenticated, confidence = service.verify(user_id="user_001", session=test_session)
    
    assert isinstance(authenticated, (bool, np.bool_))
    assert isinstance(confidence, (float, np.float64, np.float32))
    assert 0.0 <= confidence <= 1.0
    
    # 3. Check that the activity log tracking line was successfully created on disk
    assert os.path.exists(LOG_PATH) is True