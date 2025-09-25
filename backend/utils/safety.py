# backend/utils/safety.py
import re

# very lightweight list; expand later
KEYWORDS = [
    r"\bsuicide\b", r"\bsuicidal\b", r"\bkill myself\b", r"\bself[- ]?harm\b",
    r"\bcutting\b", r"\bI don'?t want to live\b", r"\bno reason to live\b",
]

SAFE_REPLY = (
    "I’m really sorry you’re going through this. I’m not a medical service, "
    "but you deserve immediate support. If you’re in danger, please contact local "
    "emergency services now. If you can, reach out to someone you trust or a mental "
    "health professional. You’re not alone. 💛"
)

def is_high_risk(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in KEYWORDS)
