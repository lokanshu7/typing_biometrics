import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TypingBiometricsService:

    def __init__(self):
        self.user_profiles = {}

    def extract_features(self, keystrokes: List[dict]) -> np.ndarray:

        if not keystrokes or len(keystrokes) < 2:
            return np.array([])

        try:
            dwell_times = [
                max(0, k["release_time"] - k["press_time"])
                for k in keystrokes
            ]

            flight_times = [
                max(
                    0,
                    keystrokes[i + 1]["press_time"]
                    - keystrokes[i]["release_time"]
                )
                for i in range(len(keystrokes) - 1)
            ]

            digraph_times = [
                max(
                    0,
                    keystrokes[i + 1]["press_time"]
                    - keystrokes[i]["press_time"]
                )
                for i in range(len(keystrokes) - 1)
            ]

            duration = (
                keystrokes[-1]["release_time"]
                - keystrokes[0]["press_time"]
            )

            typing_speed = (
                len(keystrokes) / duration * 1000
                if duration > 0 else 0
            )

            backspace_count = sum(
                1
                for k in keystrokes
                if k.get("key", "").lower() == "backspace"
            )

            backspace_rate = (
                backspace_count / len(keystrokes)
                if len(keystrokes) > 0 else 0
            )

            pauses = [
                f for f in flight_times
                if f > 500
            ]

            pause_count = len(pauses)

            avg_pause_duration = (
                np.mean(pauses)
                if pauses else 0
            )

            pause_ratio = (
                pause_count / len(flight_times)
                if flight_times else 0
            )

            features = [
                np.mean(dwell_times),
                np.std(dwell_times),
                np.median(dwell_times),
                np.percentile(dwell_times, 25),
                np.percentile(dwell_times, 75),

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

                np.max(dwell_times),
                np.min(dwell_times),

                np.max(flight_times) if flight_times else 0,
                np.min(flight_times) if flight_times else 0,

                np.var(dwell_times),

                duration,

                pause_ratio,

                backspace_count
            ]

            return np.array(features, dtype=float)

        except Exception as e:
            logger.error(
                f"Feature extraction failed: {e}"
            )
            return np.array([])

    def enroll_user(
        self,
        user_id: str,
        sessions: List[dict]
    ) -> Dict:

        logger.info(
            f"User {user_id} enrollment started"
        )

        feature_vectors = []

        for session in sessions:

            if "keystrokes" not in session:
                continue

            features = self.extract_features(
                session["keystrokes"]
            )

            if len(features) > 0:
                feature_vectors.append(features)

        if len(feature_vectors) < 3:
            return {
                "success": False,
                "message": "Minimum 3 valid sessions required."
            }

        feature_matrix = np.array(feature_vectors)

        profile = {
            "mean": np.mean(feature_matrix, axis=0),
            "std": np.std(feature_matrix, axis=0),
            "median": np.median(feature_matrix, axis=0),
            "samples": feature_vectors,
            "enrolled_at": datetime.now().isoformat(),
            "sample_count": len(feature_vectors)
        }

        self.user_profiles[user_id] = profile

        logger.info(
            f"User {user_id} enrolled successfully"
        )

        return {
            "success": True,
            "sample_count": len(feature_vectors),
            "message": "Enrollment successful"
        }

    def authenticate(
        self,
        user_id: str,
        session: dict,
        threshold: float = 0.70
    ) -> Tuple[bool, float]:

        if user_id not in self.user_profiles:
            return False, 0.0

        if "keystrokes" not in session:
            return False, 0.0

        features = self.extract_features(
            session["keystrokes"]
        )

        if len(features) == 0:
            return False, 0.0

        profile = self.user_profiles[user_id]

        mean_features = profile["mean"]
        std_features = profile["std"] + 1e-6

        normalized_diff = (
            features - mean_features
        ) / std_features

        euclidean_distance = np.linalg.norm(
            normalized_diff
        )

        similarity_score = max(
            0.0,
            1 - (euclidean_distance / 5.0)
        )

        sample_scores = []

        for sample in profile["samples"]:

            distance = np.linalg.norm(
                (features - sample)
                / std_features
            )

            score = max(
                0.0,
                1 - (distance / 3.0)
            )

            sample_scores.append(score)

        nearest_sample_score = (
            max(sample_scores)
            if sample_scores else 0.0
        )

        confidence = (
            similarity_score * 0.5
            + nearest_sample_score * 0.5
        )

        confidence = max(
            0.0,
            min(1.0, confidence)
        )

        confidence = round(
            confidence,
            3
        )

        authenticated = (
            confidence >= threshold
        )

        logger.info(
            f"User={user_id} "
            f"Auth={authenticated} "
            f"Confidence={confidence}"
        )

        return authenticated, confidence

    def get_user_profile(
        self,
        user_id: str
    ) -> Optional[Dict]:

        if user_id not in self.user_profiles:
            return None

        profile = self.user_profiles[user_id]

        return {
            "user_id": user_id,
            "sample_count": profile["sample_count"],
            "enrolled_at": profile["enrolled_at"],
            "feature_means": profile["mean"].tolist()
        }

    def list_users(self) -> List[str]:
        return list(self.user_profiles.keys())
