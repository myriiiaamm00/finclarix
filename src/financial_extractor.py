"""Deterministic, rule-based extraction of monetary figures and computed
financial exposures from contract clause text.

Everything here is plain regex + arithmetic — no AI involved — so the
"financial exposure summary" works whether or not ANTHROPIC_API_KEY is set.
AI explanations may *describe* these numbers in nicer prose, but the numbers
themselves always come from this module.
"""

import re

_CURRENCY = r'[€$£]\s?\d[\d,]*(?:\.\d{1,2})?'
_AMOUNT_RE = re.compile(_CURRENCY)

_WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}
_NUM_TO_WORD = {v: k for k, v in _WORD_TO_NUM.items()}

_RENT_PATTERNS = [
    re.compile(r'(?:monthly\s+rent|rent\s+is|rent\s+of)\s*(?:is\s*)?[:\s]*(' + _CURRENCY + r')', re.IGNORECASE),
    re.compile(r'(' + _CURRENCY + r')\s*(?:per\s+month|/\s*month|monthly)', re.IGNORECASE),
]


def _to_float(amount_str: str) -> float | None:
    """'€1,350.00' -> 1350.0"""
    m = _AMOUNT_RE.search(amount_str)
    if not m:
        return None
    digits = re.sub(r'[^\d.]', '', m.group().replace(',', ''))
    try:
        return float(digits)
    except ValueError:
        return None


def _symbol_of(amount_str: str) -> str:
    for ch in amount_str:
        if ch in "€$£":
            return ch
    return "€"


def _fmt(amount: float, symbol: str = "€") -> str:
    """1350.0 -> '€1,350' ; 75.5 -> '€75.50'"""
    if amount == int(amount):
        return f"{symbol}{int(amount):,}"
    return f"{symbol}{amount:,.2f}"


def _number_word(n: int) -> str:
    return _NUM_TO_WORD.get(n, str(n))


def _amounts_near_phrase(text: str, phrase: str, max_distance: int = 80) -> list[tuple[float, str]]:
    """For every occurrence of `phrase` (case-insensitive), find the nearest
    currency amount by absolute character distance — so e.g. 'late fee' picks
    up the nearby €75 rather than an unrelated €-figure mentioned elsewhere
    in the clause (like the monthly rent). Returns one entry per occurrence,
    in the order the phrase appears."""
    lower = text.lower()
    needle = phrase.lower()
    plen = len(phrase)
    out: list[tuple[float, str]] = []
    search_from = 0
    while True:
        idx = lower.find(needle, search_from)
        if idx == -1:
            break
        anchor = idx + plen / 2
        best: tuple[float, str] | None = None
        best_dist = None
        for m in _AMOUNT_RE.finditer(text):
            dist = abs((m.start() + m.end()) / 2 - anchor)
            if dist > max_distance:
                continue
            if best_dist is None or dist < best_dist:
                val = _to_float(m.group())
                if val is not None:
                    best, best_dist = (val, m.group().strip()), dist
        if best:
            out.append(best)
        search_from = idx + plen
    return out


def _amount_near_phrase(text: str, phrase: str, max_distance: int = 80) -> tuple[float, str] | None:
    """Convenience wrapper — nearest amount to the FIRST occurrence of `phrase`."""
    found = _amounts_near_phrase(text, phrase, max_distance)
    return found[0] if found else None


def find_amounts(text: str) -> list[tuple[float, str]]:
    """Return [(value, raw_string), ...] for every currency amount found, in order."""
    out = []
    for m in _AMOUNT_RE.finditer(text):
        val = _to_float(m.group())
        if val is not None:
            out.append((val, m.group().strip()))
    return out


def find_month_multiplier(text: str) -> int | None:
    """Pull a 'number of months' figure out of phrases like 'three months',
    '12 months', or 'one-year terms' (treated as 12 months)."""
    m = re.search(r'\b(\d{1,2})\s*[- ]?months?\b', text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r'\b(' + "|".join(_WORD_TO_NUM) + r')[- ]?months?\b', text, re.IGNORECASE)
    if m:
        return _WORD_TO_NUM[m.group(1).lower()]
    if re.search(r'\bone[- ]year\b', text, re.IGNORECASE):
        return 12
    return None


def find_rent_amount(clauses: list[str]) -> tuple[float, str] | None:
    """Locate the recurring monthly-rent figure — e.g. 'The monthly rent is
    €1,350.00' — used as the base for derived exposures (termination,
    renewal, etc.). Returns (value, currency_symbol) or None."""
    for pattern in _RENT_PATTERNS:
        for clause in clauses:
            m = pattern.search(clause)
            if m:
                val = _to_float(m.group(1))
                if val:
                    return val, _symbol_of(m.group(1))
    return None


def extract_clause_exposure(clause: str, rent: tuple[float, str] | None) -> dict | None:
    """Try to derive ONE financial-exposure line item from a single clause
    using simple keyword + amount rules. Returns {"amount": float, "text": str}
    or None if nothing could be deterministically derived."""
    lower = clause.lower()
    items: list[dict] = []

    # Non-refundable administrative deposit / fee
    if "non-refundable" in lower and ("deposit" in lower or "fee" in lower):
        found = (
            _amount_near_phrase(clause, "non-refundable")
            or _amount_near_phrase(clause, "administrative deposit")
        )
        if found:
            val, raw = found
            label = "administrative deposit" if "administrative" in lower else "deposit"
            items.append({"amount": val, "text": f"{_fmt(val, _symbol_of(raw))} non-refundable {label}"})

    # Refundable security deposit — "security deposit" can also appear in a
    # section heading next to the non-refundable figure, so walk every
    # occurrence and take the first amount not already claimed above.
    if "security deposit" in lower:
        for val, raw in _amounts_near_phrase(clause, "security deposit"):
            if not any(it["amount"] == val for it in items):
                items.append({"amount": val, "text": f"{_fmt(val, _symbol_of(raw))} security deposit"})
                break

    # Late fee
    if "late fee" in lower:
        found = _amount_near_phrase(clause, "late fee")
        if found:
            val, raw = found
            items.append({"amount": val, "text": f"{_fmt(val, _symbol_of(raw))} late fee"})

    # Early termination penalty (often expressed as N months of rent)
    if "early termination" in lower or "liquidated damages" in lower:
        months = find_month_multiplier(clause)
        if months and rent:
            rent_val, symbol = rent
            total = months * rent_val
            items.append({
                "amount": total,
                "text": (
                    f"{_fmt(total, symbol)} early termination penalty based on "
                    f"{_number_word(months)} months of {_fmt(rent_val, symbol)} rent"
                ),
            })

    # Automatic renewal exposure (full new term at current/likely rent)
    if "automatic" in lower and "renew" in lower:
        months = find_month_multiplier(clause) or 12
        if rent:
            rent_val, symbol = rent
            total = months * rent_val
            items.append({
                "amount": total,
                "text": (
                    f"up to {_fmt(total, symbol)} automatic renewal exposure based on "
                    f"{months} months of {_fmt(rent_val, symbol)} rent"
                ),
            })

    return items


def build_exposure_summary(clauses: list[str]) -> list[dict]:
    """Scan every clause and deterministically derive a list of financial
    exposure line items, e.g. {"amount": 4050.0, "text": "€4,050 early
    termination penalty based on three months of €1,350 rent"}.

    Returns [] if no monetary figures could be confidently extracted —
    callers should hide the summary section in that case.
    """
    rent = find_rent_amount(clauses)
    items: list[dict] = []
    seen: set[str] = set()
    for clause in clauses:
        for item in extract_clause_exposure(clause, rent):
            if item["text"] not in seen:
                seen.add(item["text"])
                items.append(item)
    return items
