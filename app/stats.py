"""
Word count statistics for Sunny Whisper.
Stores daily word counts in CACHE_DIR/stats.json.
Format: {"2026-03-31": 42, "2026-03-30": 5, ...}
"""

import json
from datetime import date, timedelta
from config import CACHE_DIR

_STATS_FILE = CACHE_DIR / "stats.json"

def record_words(count: int):
    """Increment word count for today."""
    stats = _load()
    today = date.today().isoformat()
    stats[today] = stats.get(today, 0) + count
    _save(stats)

def get_today() -> int:
    return _load().get(date.today().isoformat(), 0)

def get_this_week() -> int:
    week_start = date.today() - timedelta(days=date.today().weekday())
    return sum(
        words for day, words in _load().items()
        if date.fromisoformat(day) >= week_start
    )

def get_all_time() -> int:
    return sum(_load().values())

def _load() -> dict:
    if _STATS_FILE.exists():
        try:
            with open(_STATS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save(stats: dict):
    with open(_STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)
