import json
import os
import hashlib
import binascii
import ctypes
from datetime import datetime
from typing import Dict, Any, List, Optional

class FortressConfig:
    def __init__(self):
        self.app_data_dir = os.path.join(os.environ.get('APPDATA', ''), 'FocusFortress')
        self.config_file = os.path.join(self.app_data_dir, 'fortress_settings.json')
        self.settings: Dict[str, Any] = {
            "blocked_sites": [],
            "blocked_apps": [], # List of process names (e.g. "Discord.exe")
            "is_locked": False,
            "lock_end_time": None, # Timestamp
            "password_hash": None,
            "salt": None,
            "emergency_password_hash": None,
            "emergency_salt": None,
            "keywords": ["social", "game", "movie", "tiktok", "facebook", "youtube"],
            "wildcards": ["*.example.com"],
            "focus_mode": "IDLE", # IDLE, POMODORO, DEEP_WORK, EXAM_MODE
            "schedule": {
                "daily_blocks": [], # [{"start": "08:00", "end": "12:00", "days": [0,1,2,3,4]}]
                "night_mode": False
            },
            "analytics": {
                "study_time_total": 0,
                "distraction_attempts": 0,
                "sessions_completed": 0,
                "history": [] # [{"date": "2026-03-13", "focus_score": 85, "time": 120}]
            },
            "restrictions": {
                "disable_task_mgr": True,
                "disable_cmd": False,
                "disable_reg_edit": False,
                "lock_settings": False
            },
            "permanent_blocks": {
                "sites": {}, # {"domain.com": expiration_timestamp}
                "apps": {}   # {"Discord.exe": expiration_timestamp}
            },
            "headless_mode": False # If True, runs without GUI
        }
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir)
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.settings.update(data)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save_config(self):
        try:
            if not os.path.exists(self.app_data_dir):
                os.makedirs(self.app_data_dir)
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def set_password(self, password):
        if not password:
            self.settings["password_hash"] = None
            self.settings["salt"] = None
        else:
            salt = os.urandom(32)
            hash_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            self.settings["salt"] = binascii.hexlify(salt).decode('utf-8')
            self.settings["password_hash"] = binascii.hexlify(hash_key).decode('utf-8')
        self.save_config()

    def verify_password(self, password):
        if not self.settings.get("password_hash") or not self.settings.get("salt"):
            return True
        salt = binascii.unhexlify(self.settings["salt"].encode('utf-8'))
        stored_hash = self.settings["password_hash"]
        hash_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        computed_hash = binascii.hexlify(hash_key).decode('utf-8')
        return computed_hash == stored_hash

    def is_currently_locked(self):
        if self.settings.get("is_locked"):
            end_time = self.settings.get("lock_end_time")
            if end_time is None:
                return True # Manual/Infinite lock
                
            if isinstance(end_time, (int, float)):
                if datetime.now().timestamp() < end_time:
                    return True
                else:
                    # Lock expired
                    self.settings["is_locked"] = False
                    self.settings["lock_end_time"] = None
                    self.save_config()
        
        # Check if any permanent block is active
        now = datetime.now().timestamp()
        for site, expiry in self.settings.get("permanent_blocks", {}).get("sites", {}).items():
            if now < expiry: return True
        for app, expiry in self.settings.get("permanent_blocks", {}).get("apps", {}).items():
            if now < expiry: return True
            
        return False

    def add_permanent_block(self, item_type, item, days=30):
        """item_type: 'sites' or 'apps'"""
        expiry = datetime.now().timestamp() + (days * 24 * 60 * 60)
        self.settings["permanent_blocks"][item_type][item] = expiry
        self.save_config()

    def get_active_permanent_blocks(self, item_type):
        now = datetime.now().timestamp()
        active = []
        expired = []
        for item, expiry in self.settings["permanent_blocks"][item_type].items():
            if now < expiry:
                active.append((item, expiry))
            else:
                expired.append(item)
        
        # Cleanup expired
        if expired:
            for item in expired:
                del self.settings["permanent_blocks"][item_type][item]
            self.save_config()
            
        return active
