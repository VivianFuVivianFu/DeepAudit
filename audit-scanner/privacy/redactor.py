import re
from typing import Dict

PII_PATTERNS = {
    "emails": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "phones": re.compile(
        r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b"
    ),
    "ids": re.compile(r"\b(?:ssn|ssn:)?\s*\d{3}-\d{2}-\d{4}\b", re.IGNORECASE),
}


def redact(text: str) -> Dict[str, object]:
    """Redact common PII patterns from text and return stats.

    Returns: {"redacted_text": str, "counts": {pattern: int}}
    """
    if not text:
        return {"redacted_text": "", "counts": {k: 0 for k in PII_PATTERNS}}

    counts = {k: 0 for k in PII_PATTERNS}
    redacted = text

    for name, pattern in PII_PATTERNS.items():
        matches = pattern.findall(redacted)
        counts[name] = len(matches)
        if matches:
            redacted = pattern.sub(f"[REDACTED_{name.upper()}]", redacted)

    return {"redacted_text": redacted, "counts": counts}
