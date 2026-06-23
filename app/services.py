import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TypingBiometricsService:

    def __init__(self):
        self.user_profiles: Dict[str, Dict] = {}

    # ---------------- FEATURE ENGINEERING ----------------
    def extract_features(self, keystrokes: List[dict]) -> np.ndarray:

        if not keystrokes or len(keystrokes) < 2:
            return np.array([])

        try:
            dwell_times = [
                max(0, k["release_time"] - k["press_time"])
                for k in keystrokes
            ]

            flight_times = [
                max(0, keystrokes[i + 1]["press_time"] - keystrokes[i]["release_time"])
                for i in range(len(keystrokes) - 1)
            ]

            digraph_times = [
                max(0, keystrokes[i + 1]["press_time"] - keystrokes[i]["press_time"])
                for i in range(len(keystrokes) - 1)
            ]

            duration = keystrokes[-1]["release_time"] - keystrokes[0]["press_time"]
            duration = max(duration, 1)

            typing_speed = len(keystrokes) / duration * 1000

            backspace_count = sum(
                1 for k in keystrokes
                if k.get("key", "").lower() == "backspace"
            )

            backspace_rate = backspace_count / len(keystrokes) if keystrokes else 0

            pauses = [f for f in flight_times if f > 500]
            pause_count = len(pauses)

            avg_pause_duration = np.mean(pauses) if pauses else 0
            pause_ratio = pause_count / len(flight_times) if flight_times else 0

            # SAFE feature builder
            features = [
                np.mean(dwell_times) if dwell_times else 0,
                np.std(dwell_times) if dwell_times else 0,
                np.median(dwell_times) if dwell_times else 0,
                np.percentile(dwell_times, 25) if dwell_times else 0,
                np.percentile(dwell_times, 75) if dwell_times else 0,

                np.mean(flight_times) if flight_times else 0,
                np.std(flight_times) if flight_times else 0,
                np.median(flight_times) if flight_times else 0,

                np.mean(digraph_times) if digraph_times else 0,
                np.std(digraph_times) if digraph_times else 0,
                np.max(digraph_times) if digraph_times else 0,
                np.min(digraph_times) if digraph_times else 0,

                typing_speed,
                backspace_rate,
                pause_count,
                avg_pause_duration,

                np.max(dwell_times) if dwell_times else 0,
                np.min(dwell_times) if dwell_times else 0,

                np.max(flight_times) if flight_times else 0,
                np.min(flight_times) if flight_times else 0,

                np.var(dwell_times) if dwell_times else 0,

                duration,
                pause_ratio,
                backspace_count
            ]

            return np.array(features, dtype=float)

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return np.array([])

    # ---------------- ENROLLMENT ----------------
    def enroll_user(self, user_id: str, sessions: List[dict]) -> Dict:

        logger.info(f"Enrollment started: {user_id}")

        feature_vectors = []

        for session in sessions:
            ks = session.get("keystrokes", [])
            features = self.extract_features(ks)

            if len(features) > 0:
                feature_vectors.append(features)

        if len(feature_vectors) < 3:
            return {
                "success": False,
                "message": "Minimum 3 valid sessions required"
            }

        matrix = np.array(feature_vectors)

        self.user_profiles[user_id] = {
            "mean": np.mean(matrix, axis=0),
            "std": np.std(matrix, axis=0) + 1e-6,
            "median": np.median(matrix, axis=0),
            "samples": feature_vectors,
            "enrolled_at": datetime.now().isoformat(),
            "sample_count": len(feature_vectors)
        }

        return {
            "success": True,
            "message": "Enrollment successful"
        }

    # ---------------- AUTHENTICATION ----------------
    def authenticate(self, user_id: str, session: dict, threshold: float = 0.70) -> Tuple[bool, float]:

        if user_id not in self.user_profiles:
            return False, 0.0

        features = self.extract_features(session.get("keystrokes", []))

        if len(features) == 0:
            return False, 0.0

        profile = self.user_profiles[user_id]

        mean = profile["mean"]
        std = profile["std"]

        norm_diff = (features - mean) / std
        distance = np.linalg.norm(norm_diff)

        similarity = max(0.0, 1 - distance / 5.0)

        sample_scores = [
            max(0.0, 1 - np.linalg.norm((features - s) / std) / 3.0)
            for s in profile["samples"]
        ]

        nearest = max(sample_scores) if sample_scores else 0.0

        confidence = 0.5 * similarity + 0.5 * nearest
        confidence = round(max(0.0, min(1.0, confidence)), 3)

        return confidence >= threshold, confidence

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
