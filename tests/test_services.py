import pytest
import sys
sys.path.insert(0, '../app')
from services import TypingBiometricsService

def test_feature_extraction():
    service = TypingBiometricsService()
    keystrokes = [{'key': 'a', 'press_time': 100, 'release_time': 150},
                 {'key': 'b', 'press_time': 200, 'release_time': 250}]
    features = service.extract_features(keystrokes)
    assert len(features) > 0
