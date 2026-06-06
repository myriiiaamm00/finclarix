"""0-cost, runtime translation of FinClariX's deterministic clause text.

Why this exists
---------------
`src/i18n.py` already translates *static* UI chrome (buttons, badges, section
headers, …) via small per-language lookup tables — perfect for short, finite
strings. It deliberately does NOT translate the long, freely-composed English
sentences produced by `src/clause_breakdown.py` (Plain-language explanation /
Why it matters / Potential financial impact / Suggested action) or by
`src/financial_extractor.py` (Financial Exposure Summary lines): pre-writing
those by hand in 14 languages is impractical, and naive fragment-by-fragment
substitution produces grammatically broken sentences (see the module
docstring in i18n.py for details).

This module solves that the other way around: it calls a FREE machine
translation API at *runtime* to translate the already-composed English
sentence as a whole, so every user gets "mother-tongue" explanations with:
  * NO Anthropic/Claude API key required, and
  * NO paid translation subscription required.

Switching providers (Google Translate Free  ⇄  DeepL Free)
-----------------------------------------------------------
Two free backends are supported, both reachable with nothing but the Python
standard library (`urllib` + `json` — no new third-party dependency, so
nothing new to install or pay for):

  1. "google" (DEFAULT) — the unofficial public endpoint behind
     translate.google.com (`translate.googleapis.com/translate_a/single`).
     No signup, no API key. It's *unofficial* and rate-limited, so it can
     occasionally fail under heavy use — exactly why every call below is
     wrapped in a try/except with a graceful English fallback.

  2. "deepl" — DeepL's official Free API tier. Genuinely free (large
     monthly character quota) but DOES require a free API key — sign up at
     https://www.deepl.com/pro-api and put it in `.env` as `DEEPL_API_KEY`.
     Translation quality is generally higher than the Google endpoint above.

To switch providers, set the environment variable
`FINCLARIX_TRANSLATE_PROVIDER` to `"google"` or `"deepl"` (e.g. in `.env`),
or simply edit the `_PROVIDER` default below. No other code changes needed —
`translate_text()` dispatches to whichever backend is configured and falls
back to English on any failure either way.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache

# ── Provider switch ──────────────────────────────────────────────────────────
# "google" → free, no signup, unofficial endpoint (default, zero setup)
# "deepl"  → free tier, requires DEEPL_API_KEY in the environment / .env
#
# Example to switch to DeepL: set FINCLARIX_TRANSLATE_PROVIDER=deepl and
# DEEPL_API_KEY=your-free-key in your .env file — no code edits required.
_PROVIDER = os.getenv("FINCLARIX_TRANSLATE_PROVIDER", "google").strip().lower()

_REQUEST_TIMEOUT = 6  # seconds — fail fast rather than freeze the Streamlit UI

# FinClariX's display language names (see `_LANGUAGES` in app.py, which match
# the keys of `_STRINGS` in src/i18n.py) mapped to the language codes the two
# free providers expect. Google and DeepL both accept plain ISO-639-1 codes
# for every language here except Chinese, which is special-cased in each
# provider function below (Google wants "zh-CN", DeepL wants "ZH").
_LANG_CODES = {
    "English": "en",
    "Spanish": "es",
    "Chinese": "zh",
    "Dutch": "nl",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Polish": "pl",
    "Romanian": "ro",
    "Swedish": "sv",
    "Czech": "cs",
    "Hungarian": "hu",
    "Greek": "el",
}

_GOOGLE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"
_DEEPL_ENDPOINT = "https://api-free.deepl.com/v2/translate"


def _google_translate(text: str, target_code: str, source_code: str = "en") -> str:
    """Call the free, unofficial Google Translate web endpoint (the same one
    translate.google.com's web widget uses — no API key, no signup).

    Raises on any failure (network error, bad response, rate limit, …) —
    callers are expected to catch that and fall back to the English text."""
    google_target = "zh-CN" if target_code == "zh" else target_code
    params = {
        "client": "gtx",   # public web-widget client id
        "sl": source_code,
        "tl": google_target,
        "dt": "t",         # "t" = return translated text
        "q": text,
    }
    url = f"{_GOOGLE_ENDPOINT}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT) as response:
        payload = json.loads(response.read().decode("utf-8"))
    # Response shape: [[[translated_chunk, original_chunk, ...], ...], ...] —
    # long input is returned in several chunks that need rejoining in order.
    return "".join(chunk[0] for chunk in payload[0] if chunk and chunk[0])


def _deepl_translate(text: str, target_code: str, source_code: str = "en") -> str:
    """Call DeepL's official Free-tier REST API. Requires `DEEPL_API_KEY`
    (a genuinely free key from https://www.deepl.com/pro-api).

    Raises on any failure, including a missing key — callers fall back to
    English exactly as with the Google path above. This keeps the app fully
    functional even if someone sets FINCLARIX_TRANSLATE_PROVIDER=deepl
    without configuring a key."""
    api_key = os.getenv("DEEPL_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("DEEPL_API_KEY is not set — cannot use the DeepL backend")

    deepl_target = "ZH" if target_code == "zh" else target_code.upper()
    data = urllib.parse.urlencode(
        {
            "auth_key": api_key,
            "text": text,
            "source_lang": source_code.upper(),
            "target_lang": deepl_target,
        }
    ).encode("utf-8")
    request = urllib.request.Request(_DEEPL_ENDPOINT, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["translations"][0]["text"]


def _translate_uncached(text: str, lang: str) -> str:
    """Dispatch to whichever provider `_PROVIDER` selects. Raises on failure
    (network error, quota exceeded, malformed response, missing DeepL key,
    unsupported language, …) so `_cached_translate` can catch it uniformly."""
    target_code = _LANG_CODES.get(lang)
    if not target_code or target_code == "en":
        return text
    backend = _deepl_translate if _PROVIDER == "deepl" else _google_translate
    return backend(text, target_code)


@lru_cache(maxsize=1024)
def _cached_translate(text: str, lang: str) -> tuple[str, bool]:
    """Memoised translation lookup.

    FinClariX's deterministic breakdown text is templated (see the
    `_WHY_TEMPLATES` / `_ACTION_TEMPLATES` tables in clause_breakdown.py), so
    many clauses — and many reruns of the same analysis after a language
    switch — end up translating *identical* English sentences. Caching by
    (text, lang) avoids redundant network round-trips, keeps the UI snappy,
    and is gentle on the free (rate-limited) Google endpoint.

    Returns (text, ok):
      * ok=True  → `text` is the successfully translated string
      * ok=False → translation failed; `text` is the original English,
                    unchanged, ready to display as-is
    """
    try:
        translated = _translate_uncached(text, lang)
        if translated and translated.strip():
            return translated, True
        return text, False
    except Exception:
        # Any failure — quota exceeded, network error, malformed response,
        # missing DeepL key, … — degrades to "show the English original"
        # rather than ever breaking the page. Callers surface a small
        # "Translation unavailable, showing English" notice when ok=False.
        return text, False


def translate_text(text: str, lang: str) -> tuple[str, bool]:
    """Translate `text` (assumed to be English) into the FinClariX display
    language `lang`, using a free machine-translation backend.

    Always returns something safely displayable:
      * lang == "English" (or unrecognised, or empty text) → (text, True)
      * translation succeeds                               → (translated, True)
      * translation fails (quota / network / bad response) → (text, False)

    Callers should display `text` either way, and show a small
    "Translation unavailable, showing English" notice whenever `ok` is False
    (see `t("translation_unavailable_notice", lang)` in src/i18n.py).
    """
    if not text or not text.strip():
        return text, True
    if lang == "English" or lang not in _LANG_CODES:
        return text, True
    return _cached_translate(text, lang)
