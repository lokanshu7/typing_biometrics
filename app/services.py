import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TypingBiometricsService:
    """ML service for typing pattern analysis"""

    def __init__(self):
        self.user_profiles = {}

    def extract_features(self, keystrokes: List[dict]) -> np.ndarray:
        """Extract statistical timing features from keystroke data."""

        if len(keystrokes) < 2:
            return np.array([])

        # Dwell Time (key hold duration)
        dwell_times = [
            k["release_time"] - k["press_time"]
            for k in keystrokes
        ]

        # Flight Time (release -> next press)
        flight_times = [
            keystrokes[i + 1]["press_time"] -
            keystrokes[i]["release_time"]
            for i in range(len(keystrokes) - 1)
        ]

        # Digraph Time (press -> next press)
        digraph_times = [
            keystrokes[i + 1]["press_time"] -
            keystrokes[i]["press_time"]
            for i in range(len(keystrokes) - 1)
        ]

        features = []

        # Dwell statistics
        features.extend([
            np.mean(dwell_times),
            np.std(dwell_times),
            np.median(dwell_times),
            np.percentile(dwell_times, 25),
            np.percentile(dwell_times, 75)
        ])

        # Flight statistics
        if flight_times:
            features.extend([
                np.mean(flight_times),
                np.std(flight_times),
                np.median(flight_times)
            ])
        else:
            features.extend([0, 0, 0])

        # Digraph statistics
        if digraph_times:
            features.extend([
                np.mean(digraph_times),
                np.std(digraph_times),
                np.max(digraph_times),
                np.min(digraph_times)
            ])
        else:
            features.extend([0, 0, 0, 0])

        # Typing Speed
        duration = (
            keystrokes[-1]["release_time"]
            - keystrokes[0]["press_time"]
        )

        typing_speed = (
            len(keystrokes) / duration * 1000
            if duration > 0 else 0
        )

        features.append(typing_speed)

        return np.array(features)

    def enroll_user(
        self,
        user_id: str,
        sessions: List[dict]
    ) -> Dict:
        """Create a typing profile for a user."""

        logger.info(f"Enrolling user: {user_id}")

        feature_vectors = []

        for session in sessions:
            features = self.extract_features(
                session["keystrokes"]
            )

            if len(features) > 0:
                feature_vectors.append(features)

        if len(feature_vectors) < 3:
            return {
                "success": False,
                "message": (
                    "Insufficient valid samples. "
                    "Need at least 3 sessions."
                )
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
            f"User {user_id} enrolled with "
            f"{len(feature_vectors)} samples"
        )

        return {
            "success": True,
            "message": (
                f"User {user_id} enrolled successfully"
            ),
            "sample_count": len(feature_vectors)
        }

    def authenticate(
        self,
        user_id: str,
        session: dict,
        threshold: float = 0.7
    ) -> Tuple[bool, float]:
        """Verify user identity using typing pattern."""

        if user_id not in self.user_profiles:
            logger.warning(
                f"User {user_id} not enrolled"
            )
            return False, 0.0

        features = self.extract_features(
            session["keystrokes"]
        )

        if len(features) == 0:
            return False, 0.0

        profile = self.user_profiles[user_id]

        mean_features = profile["mean"]
        std_features = profile["std"] + 1e-6

        # Distance from user's average profile
        normalized_diff = (
            features - mean_features
        ) / std_features

        euclidean_dist = np.linalg.norm(
            normalized_diff
        )

        max_expected_dist = 5.0

        similarity = max(
            0,
            1 - (euclidean_dist / max_expected_dist)
        )

        # Compare against all enrolled samples
        sample_distances = []

        for sample in profile["samples"]:
            distance = np.linalg.norm(
                (features - sample)
                / std_features
            )

            sample_distances.append(distance)

        min_sample_dist = min(sample_distances)

        confidence = (
            similarity +
            max(0, 1 - min_sample_dist / 3)
        ) / 2

        authenticated = (
            confidence >= threshold
        )

        logger.info(
            f"Authentication for {user_id}: "
            f"{authenticated} "
            f"(confidence={confidence:.3f})"
        )

        return authenticated, confidence

    def get_user_profile(
        self,
        user_id: str
    ) -> Dict:
        """Return stored user profile."""

        if user_id not in self.user_profiles:
            return None

        profile = self.user_profiles[user_id]

        return {
            "user_id": user_id,
            "enrolled_at": profile["enrolled_at"],
            "sample_count": profile["sample_count"],
            "feature_means": (
                profile["mean"].tolist()
            )
        }

    def list_users(self) -> List[str]:
        """Return all enrolled users."""

        return list(
            self.user_profiles.keys()
        )
