import re

# very small, safe replacements — expand as we learn from users
REPLACEMENTS = {
    "machan": "friend",
    "harima": "very",
    "hariyata": "very",
    "nathi": "without",
    "badu": "stuff",
    "eka": "it",
    "mata": "to me",
    "mage": "my",
    "hari": "okay",
    "mage hithata": "in my mind",
    "stress ekak": "stress",
    "stress eka": "stress",
    "deadline eka": "deadline",
    "eka hari stress": "very stress",
    "cant": "can't",
}

def normalize_text(s: str) -> str:
    t = s.lower().strip()
    # simple token-wise replacements (keep punctuation)
    for k, v in REPLACEMENTS.items():
        t = re.sub(rf"\b{k}\b", v, t)
    # basic cleanup of repeated dots/spaces
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\.{3,}", "...", t)
    return t
