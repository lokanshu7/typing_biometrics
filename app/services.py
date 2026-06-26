import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
import os
import pickle
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_PATH = "data/profiles.pkl"
LOG_PATH = "data/activity_log.jsonl"


class TypingBiometricsService:

    def __init__(self):
        self.user_profiles: Dict[str, Dict] = {}
        self._load_profiles()

    # ---------------- SAVE / LOAD ----------------
    def _save_profiles(self):
        os.makedirs("data", exist_ok=True)
        with open(DATA_PATH, "wb") as f:
            pickle.dump(self.user_profiles, f)

    def _load_profiles(self):
        if os.path.exists(DATA_PATH):
            try:
                with open(DATA_PATH, "rb") as f:
                    self.user_profiles = pickle.load(f)
            except Exception as e:
                logger.error(f"Failed to load profiles pickling database: {e}")
                self.user_profiles = {}
        else:
            self.user_profiles = {}

    def _log(self, event: Dict):
        os.makedirs("data", exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(event) + "\n")

    # ---------------- FEATURE ENGINEERING ----------------
    def extract_features(self, keystrokes: List[dict]) -> np.ndarray:
        if not keystrokes or len(keystrokes) < 2:
            return np.array([])

        try:
            dwell_times = [max(0.0, k['release_time'] - k['press_time']) for k in keystrokes]
            
            flight_times = []
            for i in range(len(keystrokes) - 1):
                flight = max(0.0, keystrokes[i+1]['press_time'] - keystrokes[i]['release_time'])
                flight_times.append(flight)

            digraph_times = []
            for i in range(len(keystrokes) - 1):
                digraph = max(0.0, keystrokes[i+1]['press_time'] - keystrokes[i]['press_time'])
                digraph_times.append(digraph)

            duration = max(keystrokes[-1]['release_time'] - keystrokes[0]['press_time'], 1.0)
            typing_speed = (len(keystrokes) / duration) * 1000

            backspace_count = sum(1 for k in keystrokes if str(k.get('key', '')).lower() == 'backspace')
            backspace_rate = backspace_count / len(keystrokes)

            pauses = [f for f in flight_times if f > 500.0]
            pause_count = len(pauses)
            avg_pause_duration = float(np.mean(pauses)) if pauses else 0.0
            pause_ratio = pause_count / len(flight_times) if flight_times else 0.0

            features = [
                float(np.mean(dwell_times)) if dwell_times else 0.0,
                float(np.std(dwell_times)) if dwell_times else 0.0,
                float(np.median(dwell_times)) if dwell_times else 0.0,
                float(np.percentile(dwell_times, 25)) if dwell_times else 0.0,
                float(np.percentile(dwell_times, 75)) if dwell_times else 0.0,

                float(np.mean(flight_times)) if flight_times else 0.0,
                float(np.std(flight_times)) if flight_times else 0.0,
                float(np.median(flight_times)) if flight_times else 0.0,

                float(np.mean(digraph_times)) if digraph_times else 0.0,
                float(np.std(digraph_times)) if digraph_times else 0.0,
                float(np.max(digraph_times)) if digraph_times else 0.0,
                float(np.min(digraph_times)) if digraph_times else 0.0,

                float(typing_speed),
                float(backspace_rate),
                float(pause_count),
                float(avg_pause_duration),

                float(np.max(dwell_times)) if dwell_times else 0.0,
                float(np.min(dwell_times)) if dwell_times else 0.0,

                float(np.max(flight_times)) if flight_times else 0.0,
                float(np.min(flight_times)) if flight_times else 0.0,

                float(np.var(dwell_times)) if dwell_times else 0.0,
                float(duration),
                float(pause_ratio),
                float(backspace_count)
            ]
            return np.array(features, dtype=float)

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return np.array([])

    # ---------------- ENROLL ----------------
    def enroll_user(self, user_id: str, sessions: List[dict]) -> Dict:
        feature_vectors = []

        for session in sessions:
            ks = session.get("keystrokes", [])
            features = self.extract_features(ks)
            if len(features) > 0:
                feature_vectors.append(features)

        if len(feature_vectors) < 3:
            return {"success": False, "message": f"Minimum 3 sessions required. Captured: {len(feature_vectors)}"}

        matrix = np.array(feature_vectors)

        scaler = StandardScaler()
        scaled = scaler.fit_transform(matrix)

        # Set contamination safely for a small pool of samples
        iso = IsolationForest(contamination=0.1, random_state=42)
        iso.fit(scaled)

        oc_svm = OneClassSVM(kernel='rbf', gamma='auto', nu=0.1)
        oc_svm.fit(scaled)

        self.user_profiles[user_id] = {
            "mean": np.mean(matrix, axis=0),
            "std": np.std(matrix, axis=0) + 1e-6,
            "samples": feature_vectors,
            "scaler": scaler,
            "iso_model": iso,
            "oc_svm": oc_svm,
            "enrolled_at": datetime.now().isoformat(),
            "sample_count": len(feature_vectors)
        }

        self._save_profiles()
        logger.info(f"User {user_id} enrolled successfully with {len(feature_vectors)} samples.")

        self._log({
            "event": "enroll",
            "user_id": user_id,
            "time": datetime.now().isoformat()
        })

        return {
            "success": True, 
            "message": f"User {user_id} enrolled successfully", 
            "sample_count": len(feature_vectors)
        }

    # ---------------- VERIFY / AUTHENTICATE ----------------
    def authenticate(self, user_id: str, session: dict, threshold: float = 0.5) -> Tuple[bool, float]:
        if user_id not in self.user_profiles:
            return False, 0.0

        features = self.extract_features(session.get("keystrokes", []))
        if len(features) == 0:
            return False, 0.0

        profile = self.user_profiles[user_id]
        mean = profile["mean"]
        std = profile["std"]

        # 1. Z-score standard similarity
        z_score = np.linalg.norm((features - mean) / std)
        z_sim = max(0.0, 1.0 - (z_score / 5.0))

        # 2. Minimum Euclidean sample distance similarity
        sample_scores = [
            max(0.0, 1.0 - (np.linalg.norm((features - s) / std) / 3.0))
            for s in profile["samples"]
        ]
        nearest = max(sample_scores) if sample_scores else 0.0

        # 3. Isolation Forest scoring
        scaled_feat = profile["scaler"].transform([features])
        iso_score = profile["iso_model"].decision_function(scaled_feat)[0]
        iso_norm = max(0.0, min(1.0, iso_score + 0.5))

        # 4. One Class SVM prediction score
        svm_pred = profile["oc_svm"].predict(scaled_feat)[0]
        svm_score = 1.0 if svm_pred == 1 else 0.0

        # Blended mathematical ensemble model voting
        confidence = (0.35 * z_sim) + (0.25 * nearest) + (0.20 * iso_norm) + (0.20 * svm_score)
        confidence = round(max(0.0, min(1.0, confidence)), 3)
        
        authenticated = confidence >= threshold

        self._log({
            "event": "verify",
            "user_id": user_id,
            "confidence": confidence,
            "result": bool(authenticated),
            "time": datetime.now().isoformat()
        })

        return bool(authenticated), float(confidence)

    # ---------------- PROFILE ----------------
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        if user_id not in self.user_profiles:
            return None

        p = self.user_profiles[user_id]
        return {
            "user_id": user_id,
            "sample_count": p["sample_count"],
            "enrolled_at": p["enrolled_at"],
            "feature_means": p["mean"].tolist()
        }

    # ---------------- USERS LIST ----------------
    def list_users(self) -> List[str]:
        return list(self.user_profiles.keys())