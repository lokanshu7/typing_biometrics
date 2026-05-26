import numpy as np
from typing import List, Dict, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TypingBiometricsService:
    """ML service for typing pattern analysis"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.user_profiles = {}  # user_id -> feature statistics
        
    def extract_features(self, keystrokes: List[dict]) -> np.ndarray:
        """Extract timing features from keystroke data"""
        if len(keystrokes) < 2:
            return np.array([])
        
        features = []
        
        # 1. Dwell times (how long each key is held)
        dwell_times = [k['release_time'] - k['press_time'] for k in keystrokes]
        
        # 2. Flight times (time between key release and next press)
        flight_times = []
        for i in range(len(keystrokes) - 1):
            flight = keystrokes[i+1]['press_time'] - keystrokes[i]['release_time']
            flight_times.append(flight)
        
        # 3. Digraph timings (press-to-press for consecutive keys)
        digraph_times = []
        for i in range(len(keystrokes) - 1):
            digraph = keystrokes[i+1]['press_time'] - keystrokes[i]['press_time']
            digraph_times.append(digraph)
        
        # Statistical features
        features.extend([
            np.mean(dwell_times),
            np.std(dwell_times),
            np.median(dwell_times),
            np.percentile(dwell_times, 25),
            np.percentile(dwell_times, 75),
        ])
        
        if flight_times:
            features.extend([
                np.mean(flight_times),
                np.std(flight_times),
                np.median(flight_times),
            ])
        else:
            features.extend([0, 0, 0])
        
        if digraph_times:
            features.extend([
                np.mean(digraph_times),
                np.std(digraph_times),
                np.max(digraph_times),
                np.min(digraph_times),
            ])
        else:
            features.extend([0, 0, 0, 0])
        
        # Typing rhythm features
        features.append(len(keystrokes) / (keystrokes[-1]['release_time'] - keystrokes[0]['press_time']) * 1000)  # keys per second
        
        return np.array(features)
    
    def enroll_user(self, user_id: str, sessions: List[dict]) -> Dict:
        """Enroll a new user with their typing samples"""
        logger.info(f"Enrolling user: {user_id}")
        
        # Extract features from all sessions
        feature_vectors = []
        for session in sessions:
            features = self.extract_features(session['keystrokes'])
            if len(features) > 0:
                feature_vectors.append(features)
        
        if len(feature_vectors) < 3:
            return {
                'success': False,
                'message': 'Insufficient valid samples. Need at least 3 sessions.'
            }
        
        # Calculate statistics for user profile
        feature_matrix = np.array(feature_vectors)
        profile = {
            'mean': np.mean(feature_matrix, axis=0),
            'std': np.std(feature_matrix, axis=0),
            'median': np.median(feature_matrix, axis=0),
            'samples': feature_vectors,
            'enrolled_at': datetime.now().isoformat(),
            'sample_count': len(feature_vectors)
        }
        
        self.user_profiles[user_id] = profile
        logger.info(f"User {user_id} enrolled with {len(feature_vectors)} samples")
        
        return {
            'success': True,
            'message': f'User {user_id} enrolled successfully',
            'sample_count': len(feature_vectors)
        }
    
    def authenticate(self, user_id: str, session: dict, threshold: float = 0.7) -> Tuple[bool, float]:
        """Authenticate user based on typing pattern"""
        if user_id not in self.user_profiles:
            logger.warning(f"User {user_id} not enrolled")
            return False, 0.0
        
        # Extract features from authentication attempt
        features = self.extract_features(session['keystrokes'])
        if len(features) == 0:
            return False, 0.0
        
        profile = self.user_profiles[user_id]
        
        # Calculate similarity using multiple metrics
        # 1. Euclidean distance (normalized)
        mean_features = profile['mean']
        std_features = profile['std'] + 1e-6  # avoid division by zero
        
        # Normalize the difference
        normalized_diff = (features - mean_features) / std_features
        euclidean_dist = np.linalg.norm(normalized_diff)
        
        # Convert distance to similarity score (0 to 1)
        # Lower distance = higher similarity
        max_expected_dist = 5.0  # tunable parameter
        similarity = max(0, 1 - (euclidean_dist / max_expected_dist))
        
        # 2. Mahalanobis-like distance using samples
        sample_distances = []
        for sample in profile['samples']:
            dist = np.linalg.norm((features - sample) / (std_features))
            sample_distances.append(dist)
        
        min_sample_dist = min(sample_distances)
        avg_sample_dist = np.mean(sample_distances)
        
        # Combined confidence score
        confidence = (similarity + max(0, 1 - min_sample_dist/3)) / 2
        
        authenticated = confidence >= threshold
        
        logger.info(f"Authentication for {user_id}: {authenticated} (confidence: {confidence:.3f})")
        
        return authenticated, confidence
    
    def get_user_profile(self, user_id: str) -> Dict:
        """Get user profile statistics"""
        if user_id not in self.user_profiles:
            return None
        
        profile = self.user_profiles[user_id]
        return {
            'user_id': user_id,
            'enrolled_at': profile['enrolled_at'],
            'sample_count': profile['sample_count'],
            'feature_means': profile['mean'].tolist()
        }
    
    def list_users(self) -> List[str]:
        """List all enrolled users"""
        return list(self.user_profiles.keys())
