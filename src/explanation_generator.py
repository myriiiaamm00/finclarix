import os
import anthropic

_client: anthropic.Anthropic | None = None

_SYSTEM_PROMPT = (
    "You are a legal and financial contract expert helping young expats and international "
    "students understand the contracts they sign. Your job is to explain contract clauses "
    "in plain, simple language — as if explaining to a smart friend with no legal background. "
    "Be concise (2–4 sentences). Name the key risk or concern clearly. Avoid legal jargon. "
    "If the clause is genuinely problematic, say so directly."
)


def _get_client() -> anthropic.Anthropic | None:
    global _client
    if _client is None:
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            return None
        _client = anthropic.Anthropic(api_key=key)
    return _client


def explain_clause(
    clause: str,
    risk_level: str,
    matched_keywords: list[str],
    language: str = "English",
) -> str:
    client = _get_client()
    if not client:
        return "_AI explanations disabled — set ANTHROPIC_API_KEY to enable._"

    keywords_str = ", ".join(matched_keywords) if matched_keywords else "none detected"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=350,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Explain the following contract clause in plain language. "
                    f"Respond in {language}. Risk level assessed: {risk_level}. "
                    f"Flagged terms: {keywords_str}.\n\n"
                    f"Clause:\n{clause}"
                ),
            }
        ],
    )
    return response.content[0].text
