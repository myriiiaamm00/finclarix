import os
import anthropic

_client: anthropic.Anthropic | None = None

_SYSTEM_PROMPT = (
    "You're a financially sharp friend who has read way too many contracts and knows exactly "
    "where companies hide the traps. Your friend just sent you a clause they're about to sign "
    "and needs the real talk — not a lecture.\n\n"
    "Your rules:\n"
    "— 2-3 sentences MAX. No padding, no preamble.\n"
    "— Casual and direct, like texting. Zero corporate speak.\n"
    "— Say what could actually happen to them in concrete terms.\n"
    "— If it's a trap or a red flag, call it out. Don't soften it.\n"
    "— Use 'you' and 'they' — make it feel personal.\n"
    "— Never write 'it is worth noting', 'furthermore', or 'in the event that'.\n"
    "— If the clause is actually fine despite sounding scary, say so and why."
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
