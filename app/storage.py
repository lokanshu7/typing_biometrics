import json
import pickle
import logging
from pathlib import Path
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalStorage:

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.users_file = self.data_dir / "users.json"
        self.profiles_file = self.data_dir / "profiles.pkl"

    def save_user_profiles(
        self,
        profiles: Dict
    ) -> bool:

        try:
            with open(
                self.profiles_file,
                "wb"
            ) as file:
                pickle.dump(profiles, file)

            metadata = {}

            for user_id, profile in profiles.items():
                metadata[user_id] = {
                    "enrolled_at": profile.get(
                        "enrolled_at"
                    ),
                    "sample_count": profile.get(
                        "sample_count"
                    )
                }

            with open(
                self.users_file,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    metadata,
                    file,
                    indent=4
                )

            logger.info(
                "User profiles saved successfully"
            )

            return True

        except Exception as error:
            logger.error(
                f"Failed to save profiles: {error}"
            )
            return False

    def load_user_profiles(
        self
    ) -> Dict:

        try:
            if not self.profiles_file.exists():
                return {}

            with open(
                self.profiles_file,
                "rb"
            ) as file:
                profiles = pickle.load(file)

            logger.info(
                "User profiles loaded successfully"
            )

            return profiles

        except (
            pickle.UnpicklingError,
            EOFError,
            FileNotFoundError
        ) as error:

            logger.error(
                f"Failed to load profiles: {error}"
            )

            return {}

    def save_session_log(
        self,
        user_id: str,
        session_data: Dict
    ) -> bool:

        try:
            log_file = (
                self.data_dir /
                f"session_log_{user_id}.jsonl"
            )

            with open(
                log_file,
                "a",
                encoding="utf-8"
            ) as file:
                file.write(
                    json.dumps(session_data)
                    + "\n"
                )

            return True

        except Exception as error:
            logger.error(
                f"Failed to save session log: {error}"
            )
            return False

    def get_user_metadata(
        self
    ) -> Dict:

        try:
            if not self.users_file.exists():
                return {}

            with open(
                self.users_file,
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        except Exception as error:
            logger.error(
                f"Failed to read metadata: {error}"
            )
            return {}

    def delete_user(
        self,
        user_id: str
    ) -> bool:

        try:
            profiles = self.load_user_profiles()

            if user_id not in profiles:
                return False

            del profiles[user_id]

            return self.save_user_profiles(
                profiles
            )

        except Exception as error:
            logger.error(
                f"Failed to delete user: {error}"
            )
            return False
