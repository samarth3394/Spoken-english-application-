"""
Aspire English Hub - Utility Helpers
======================================
Shared utility functions.
"""

import re
import secrets
from datetime import datetime, timezone


def generate_display_name() -> str:
    """Generate a random anonymous display name."""
    adjectives = ["Swift", "Bright", "Calm", "Bold", "Keen", "Wise", "Cool", "Sharp", "Brave", "Noble"]
    nouns = ["Speaker", "Learner", "Scholar", "Voice", "Star", "Hawk", "Fox", "Eagle", "Tiger", "Lion"]
    num = secrets.randbelow(1000)
    return f"{secrets.choice(adjectives)}{secrets.choice(nouns)}{num}"


def sanitize_input(text: str) -> str:
    """Basic XSS sanitization."""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('"', '&quot;').replace("'", '&#x27;')
    return text.strip()


def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def calculate_level(xp: int) -> str:
    """Determine proficiency level based on XP."""
    if xp < 500:
        return "beginner"
    elif xp < 2000:
        return "elementary"
    elif xp < 5000:
        return "intermediate"
    elif xp < 10000:
        return "upper_intermediate"
    elif xp < 20000:
        return "advanced"
    return "proficient"
