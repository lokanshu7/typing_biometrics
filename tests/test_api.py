import pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, '../app')
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_enroll_user():
    keystrokes = [{'key': 't', 'press_time': 100, 'release_time': 150}]
    sessions = [{'user_id': 'test', 'text': 't', 'keystrokes': keystrokes,
                'session_start': 0, 'session_end': 200}] * 3
    response = client.post("/enroll", json={'user_id': 'test_user', 'sessions': sessions})
    assert response.status_code in [200, 400]
