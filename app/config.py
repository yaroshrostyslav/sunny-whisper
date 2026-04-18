"""
Configuration constants for Sunny Whisper application.
"""

import os
import sys
import json
import time
from pathlib import Path

# Application Info
APP_NAME = "Sunny Whisper"
APP_VERSION = "1.0.0"
GIT_COMMIT = "a8dcc71"
GITHUB_URL = "https://github.com/yaroshrostyslav/sunny-whisper"

# Model Configuration
HF_MODEL_REPO_ID = "SYSTRAN/faster-whisper-small"
# HF_MODEL_REPO_ID = "SYSTRAN/faster-whisper-large-v3"

# Paths
CACHE_DIR = Path.home() / "Library" / "Caches" / APP_NAME
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_CONFIG_FILE = CACHE_DIR / "user_config.json"

# Audio Configuration
FS = 44100  # Sample rate
TARGET_SR = 16000  # Target sample rate for transcription

# Transcription Configuration
BEAM_SIZE = 5

# User config defaults
_DEFAULTS = {
    "RECORD_KEYS": ["shift_r"],
    "language": "Not selected",
    "dictionary": [],
}

_VALID_LANGUAGES = {"Not selected", "en", "ru", "uk"}

# In-memory cache
_config: dict = {}

LOG_FILE = str(CACHE_DIR / "debug.log")

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def init_config():
    """Load user config from file, or create it with defaults if missing."""
    global _config
    print(f"Config dir: {_CONFIG_FILE}")
    if _CONFIG_FILE.exists():
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        _config = {**_DEFAULTS, **loaded}  # merge to handle missing keys
    else:
        _config = dict(_DEFAULTS)
        _save_config()
    if _config.get("language") not in _VALID_LANGUAGES:
        _config["language"] = "Not selected"
    if not isinstance(_config.get("dictionary"), list):
        _config["dictionary"] = []

def get_config_value(key):
    """Get a config value from the in-memory cache."""
    return _config[key]

def update_config(key, value):
    """Update a config value in memory and persist to file."""
    _config[key] = value
    _save_config()

def _save_config():
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(_config, f, indent=2, ensure_ascii=False)

def get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_icons_dir() -> str:
    base = get_base_dir()
    return base if getattr(sys, "frozen", False) else os.path.join(base, "icons")

def get_model_dir() -> str:
    base = get_base_dir()
    return os.path.join(base, "model") if getattr(sys, "frozen", False) else os.path.join(base, "app", "model")
