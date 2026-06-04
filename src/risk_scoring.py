RISK_LEVELS = ("High", "Medium", "Low", "Informational")

RISK_EMOJI = {
    "High": "🔴",
    "Medium": "🟡",
    "Low": "🟢",
    "Informational": "ℹ️",
}

RISK_COLOR = {
    "High": "#ff4b4b",
    "Medium": "#ffa500",
    "Low": "#21c354",
    "Informational": "#808080",
}


def score_clause(matches: dict[str, list[str]]) -> str:
    if matches.get("high"):
        return "High"
    if matches.get("medium"):
        return "Medium"
    if matches.get("low"):
        return "Low"
    return "Informational"


def all_keywords(matches: dict[str, list[str]]) -> list[str]:
    return matches["high"] + matches["medium"] + matches["low"]
