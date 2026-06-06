import json
from pathlib import Path


def load_keywords(path: str | Path = "data/risk_keywords.json") -> dict:
    """Load the risk-keyword lists from a JSON file.

    `path` is relative to the current working directory by default — callers
    that need launch-location independence (like app.py) should pass an
    absolute Path resolved from `Path(__file__)`.
    """
    with open(Path(path)) as f:
        return json.load(f)


def detect_risks(clause: str, keywords: dict) -> dict[str, list[str]]:
    """Return matched keyword lists per risk level for a single clause."""
    lower = clause.lower()
    matches: dict[str, list[str]] = {"high": [], "medium": [], "low": []}
    for level in ("high", "medium", "low"):
        for kw in keywords.get(level, []):
            if kw.lower() in lower:
                matches[level].append(kw)
    return matches
