import json
import numpy as np
import os
from typing import Dict, Optional
import pickle
from pathlib import Path

class LocalStorage:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.users_file = self.data_dir / "users.json"
        self.profiles_file = self.data_dir / "profiles.pkl"
        
    def save_user_profiles(self, profiles: Dict) -> bool:
        try:
            with open(self.profiles_file, 'wb') as f:
                pickle.dump(profiles, f)
            metadata = {}
            for user_id, profile in profiles.items():
                metadata[user_id] = {
                    'enrolled_at': profile.get('enrolled_at'),
                    'sample_count': profile.get('sample_count'),
                }
            with open(self.users_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving: {e}")
            return False
    
    def load_user_profiles(self) -> Optional[Dict]:
        try:
            if self.profiles_file.exists():
                with open(self.profiles_file, 'rb') as f:
                    return pickle.load(f)
            return {}
        except Exception as e:
            return {}
    
    def save_session_log(self, user_id: str, session_data: Dict) -> bool:
        try:
            log_file = self.data_dir / f"session_log_{user_id}.jsonl"
            with open(log_file, 'a') as f:
                f.write(json.dumps(session_data) + '\n')
            return True
        except:
            return False
