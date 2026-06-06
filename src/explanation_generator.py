import os
import re

import anthropic

_client: anthropic.Anthropic | None = None

_SYSTEM_PROMPT = (
    "You're a financially sharp friend who has read way too many contracts and knows exactly "
    "where companies hide the traps. Your friend just sent you a clause they're about to sign "
    "and needs the real talk — not a lecture.\n\n"
    "Reply with EXACTLY four labelled sections, each 1-2 sentences, in this format and nothing "
    "else (use these exact labels, one per line, no extra commentary before or after):\n\n"
    "EXPLANATION: <what this clause actually says, in plain language>\n"
    "WHY_IT_MATTERS: <why your friend should care — what's really at stake for them>\n"
    "FINANCIAL_IMPACT: <put a real number on it, computed only from figures actually present "
    "in the clause — e.g. 'that late fee alone could run you €900/year if you're ever short on "
    "rent'. Never invent numbers that aren't there; if there's truly nothing to calculate, say so>\n"
    "SUGGESTED_ACTION: <one concrete thing to do before signing — push back, get it in writing, "
    "walk away, or just note it and move on>\n\n"
    "Style rules:\n"
    "— Casual and direct, like texting. Zero corporate speak.\n"
    "— Use 'you' and 'they' — make it feel personal.\n"
    "— Never write 'it is worth noting', 'furthermore', or 'in the event that'.\n"
    "— If it's a trap or a red flag, call it out. Don't soften it.\n"
    "— If the clause is actually fine despite sounding scary, say so and why."
)

_SECTION_RE = re.compile(
    r'EXPLANATION:\s*(?P<explanation>.*?)\s*'
    r'WHY_IT_MATTERS:\s*(?P<why_it_matters>.*?)\s*'
    r'FINANCIAL_IMPACT:\s*(?P<financial_impact>.*?)\s*'
    r'SUGGESTED_ACTION:\s*(?P<suggested_action>.*)',
    re.IGNORECASE | re.DOTALL,
)


def _get_client() -> anthropic.Anthropic | None:
    global _client
    if _client is None:
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            return None
        _client = anthropic.Anthropic(api_key=key)
    return _client


def _parse_sections(text: str) -> dict[str, str] | None:
    """Parse the four labelled sections out of the model's reply. Returns
    None if the expected structure isn't present, so callers can fall back
    to the deterministic breakdown instead of showing a malformed blob."""
    m = _SECTION_RE.search(text)
    if not m:
        return None
    parsed = {k: v.strip() for k, v in m.groupdict().items()}
    if not all(parsed.values()):
        return None
    return parsed


def explain_clause(
    clause: str,
    risk_level: str,
    matched_keywords: list[str],
    language: str = "English",
) -> dict[str, str] | None:
    """Ask Claude to produce an AI-polished four-part breakdown:
    explanation / why_it_matters / financial_impact / suggested_action.

    Returns None when no API key is configured, the request fails, or the
    reply can't be parsed into the expected structure — in every such case
    the caller should fall back to the deterministic breakdown so the app
    keeps working without an API key.
    """
    client = _get_client()
    if not client:
        return None

    keywords_str = ", ".join(matched_keywords) if matched_keywords else "none detected"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=450,
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
                    f"Break down the following contract clause into the four sections. "
                    f"Respond in {language}. Risk level assessed: {risk_level}. "
                    f"Flagged terms: {keywords_str}.\n\n"
                    f"Clause:\n{clause}"
                ),
            }
        ],
    )
    return _parse_sections(response.content[0].text)
