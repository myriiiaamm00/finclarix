"""Deterministic, rule-based four-part breakdown for risky clauses.

Every risky clause gets four labelled parts:
  1. Plain-language explanation
  2. Why it matters
  3. Potential financial impact
  4. Suggested action before signing

This module builds all four WITHOUT calling any AI — it works whether or not
ANTHROPIC_API_KEY is set. When the API key is available, app.py may layer an
AI-polished version on top (see explanation_generator.explain_clause), but the
deterministic version below is always the baseline so the app degrades
gracefully.
"""

from src.financial_extractor import extract_clause_exposure

_BREAKDOWN_KEYS = ("explanation", "why_it_matters", "financial_impact", "suggested_action")

# ── Clause categories ─────────────────────────────────────────────────────────
# Multiple High-risk (or Medium-risk, etc.) clauses in the same contract often
# cover very different ground — a deposit clause and an arbitration clause are
# both "high-risk" but for completely different reasons. Tagging each clause
# with a topical category lets the "why it matters" / "suggested action" text
# speak to what's ACTUALLY in that clause, instead of repeating one generic
# sentence per risk level for every clause that happens to share that level.
#
# Detection is simple substring matching against the matched risk keywords
# first (cheap, already computed) and then the raw clause text as a fallback —
# fully deterministic, no AI involved. "default" is used whenever no category
# rule matches, preserving the original generic-by-risk-level behaviour.
_CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("deposit", ("deposit", "non-refundable", "nonrefundable", "non refundable", "forfeiture")),
    ("renewal_termination", (
        "renewal", "renew", "early termination", "early cancellation", "termination",
        "cancellation", "unilateral termination",
    )),
    ("liability_arbitration", (
        "arbitration", "indemnif", "hold harmless", "liability", "waive", "waiver",
        "class action", "personal guarantee", "personal assets", "no right to sue",
    )),
    ("fees_charges", (
        "fee", "charge", "interest", "overdraft", "penalty", "variable rate",
        "credit check", "transfer fee",
    )),
    ("notice_utilities", (
        "notice", "utilities", "subletting", "sublet", "inspection", "maintenance",
        "wear and tear", "repairs",
    )),
)


def _categorise(clause_text: str, matched_keywords: list[str]) -> str:
    """Best-effort topical bucket for a clause, used to pick more specific
    template wording. Falls back to "default" when nothing matches."""
    haystacks = [k.lower() for k in matched_keywords] + [clause_text.lower()]
    for category, needles in _CATEGORY_RULES:
        for hay in haystacks:
            if any(needle in hay for needle in needles):
                return category
    return "default"


def _pick_template(table: dict, risk_level: str, category: str) -> str:
    """Look up `table[risk_level][category]`, falling back to
    `table[risk_level]["default"]`, then to the Low-risk default — so every
    combination always resolves to *something* sensible."""
    level_table = table.get(risk_level) or table.get("Low", {})
    return level_table.get(category) or level_table.get("default", "")


_WHY_TEMPLATES = {
    "High": {
        "deposit": (
            "This is a high-risk clause about money you hand over up front: phrases "
            "like 'non-refundable' mean that cash may be gone the moment you sign, "
            "regardless of how the rest of the agreement plays out."
        ),
        "renewal_termination": (
            "This is a high-risk clause about how — and how easily — the agreement "
            "can end or roll over. Automatic renewals and termination penalties are "
            "exactly the kind of thing that quietly locks you in for far longer (or "
            "costs far more) than you expected."
        ),
        "liability_arbitration": (
            "This is a high-risk clause that limits your legal options or shifts "
            "responsibility onto you — arbitration requirements, liability waivers, "
            "and indemnification language can mean you give up the right to push "
            "back later, even if something goes wrong through no fault of your own."
        ),
        "fees_charges": (
            "This is a high-risk clause built around a fee or penalty. On its own it "
            "might look like a small line item, but penalty-style charges are "
            "designed to add up quickly once they're triggered."
        ),
        "default": (
            "This is a high-risk clause: it can cost you real money or limit your "
            "rights, and once you've signed there's little room left to negotiate it away."
        ),
    },
    "Medium": {
        "deposit": (
            "This clause concerns deposits or up-front payments. It's not framed as "
            "aggressively as the high-risk clauses, but the money involved is real, "
            "and the conditions for getting it back are worth understanding now."
        ),
        "renewal_termination": (
            "This clause sets out how renewal or termination works. It's the kind of "
            "thing that reads as routine — until the date it governs actually arrives "
            "and you realise you needed to act earlier than you thought."
        ),
        "liability_arbitration": (
            "This clause touches on responsibility, disputes, or how disagreements "
            "get resolved. It carries real legal weight even though it's phrased in "
            "fairly neutral, procedural language."
        ),
        "fees_charges": (
            "This clause introduces a fee, charge, or rate that could change over "
            "time. These add up gradually rather than all at once, which is exactly "
            "why they're easy to underestimate."
        ),
        "default": (
            "This clause carries real financial or legal weight. It can look like "
            "routine boilerplate — until the day it actually applies to you."
        ),
    },
    "Low": {
        "deposit": (
            "This clause is about a deposit or refundable payment. The risk here is "
            "lower, but knowing exactly when and how you get the money back will "
            "save you a headache at move-out or account closure."
        ),
        "renewal_termination": (
            "This clause covers renewal or termination mechanics in a fairly "
            "low-risk way, but it's still the kind of detail that's much easier to "
            "deal with if you already know it's there."
        ),
        "notice_utilities": (
            "This clause is about notice periods, utilities, or day-to-day "
            "responsibilities. It's lower-risk, but missing a notice deadline or "
            "misunderstanding who pays for what is a common — and avoidable — "
            "source of friction."
        ),
        "default": (
            "On its own this clause is lower-risk, but it's still worth understanding "
            "now so it doesn't catch you off guard later."
        ),
    },
    "Informational": {
        "notice_utilities": (
            "This clause mostly describes practical, day-to-day arrangements — "
            "notice periods, utilities, maintenance — rather than creating a direct "
            "financial risk. It's useful background for living under the agreement."
        ),
        "default": (
            "This is mostly informational — it sets expectations rather than creating "
            "a direct financial risk, but it's still useful to know it's there."
        ),
    },
}

_ACTION_TEMPLATES = {
    "High": {
        "deposit": (
            "Before paying anything, get the exact conditions for refunds (or lack "
            "thereof) confirmed in writing, and photograph/document the property's "
            "condition on day one so there's no dispute later about what the deposit "
            "can be kept for."
        ),
        "renewal_termination": (
            "Mark the renewal/termination decision dates somewhere you'll actually "
            "see them, and ask in writing whether the renewal or penalty terms can "
            "be capped, shortened, or made opt-in rather than automatic."
        ),
        "liability_arbitration": (
            "Ask whether this clause can be narrowed or removed — particularly "
            "anything that waives your right to go to court — and consider having a "
            "lawyer or tenants'/consumers' advice service review it before you sign."
        ),
        "fees_charges": (
            "Get the fee amount, the conditions that trigger it, and any caps written "
            "down explicitly, and ask what happens if you're only briefly or "
            "marginally over the line."
        ),
        "default": (
            "Ask for this clause to be removed, capped, or rewritten in writing before "
            "you sign. If the other side won't budge, treat that as a warning sign about "
            "the rest of the contract."
        ),
    },
    "Medium": {
        "deposit": (
            "Confirm in writing how and when the deposit is returned, and what "
            "(if anything) it can be deducted for — then keep that confirmation "
            "alongside the signed agreement."
        ),
        "renewal_termination": (
            "Set yourself a reminder well before the relevant renewal or termination "
            "date, and ask now — while you still have leverage — whether the terms "
            "can be adjusted."
        ),
        "liability_arbitration": (
            "Ask for plain-language clarification of what this clause means in "
            "practice, and get that clarification in writing rather than relying on "
            "a verbal explanation."
        ),
        "fees_charges": (
            "Ask for a complete list of the fees and rates that could apply, including "
            "any that can change over time, and how much notice you'd get before a "
            "change takes effect."
        ),
        "default": (
            "Raise this clause before signing and get any clarification or softening in "
            "writing — don't rely on a verbal promise that 'it won't really be enforced'."
        ),
    },
    "Low": {
        "deposit": (
            "Note the refund conditions, and keep receipts or photos that document "
            "the property's or account's starting condition — small things that make "
            "a refund dispute much easier to resolve later."
        ),
        "renewal_termination": (
            "Jot down the relevant dates somewhere visible. There's no need to "
            "renegotiate now, but you'll be glad you didn't have to dig through the "
            "contract later to find them."
        ),
        "notice_utilities": (
            "Note who is responsible for what and how much notice is required, and "
            "keep a copy of the agreement where you can find it when the question "
            "actually comes up."
        ),
        "default": (
            "No need to push back hard, but make a note of it and keep a copy of the "
            "signed agreement so you can point back to it if it ever comes up."
        ),
    },
    "Informational": {
        "notice_utilities": (
            "Just note the practical details (who handles what, and on what timeline) "
            "for your own reference — no action is needed before signing."
        ),
        "default": (
            "Just note it for your records — no action needed before signing."
        ),
    },
}


def _summarise(clause_text: str, limit: int = 240) -> str:
    """Small deterministic summary: the clause text, collapsed to one line and
    trimmed to a sentence boundary near `limit` characters."""
    text = " ".join(clause_text.split())
    if len(text) <= limit:
        return text
    cutoff = text.rfind(". ", 0, limit)
    if cutoff == -1:
        cutoff = limit
    return text[:cutoff + 1].strip()


def build_breakdown(
    clause_text: str,
    risk_level: str,
    matched_keywords: list[str],
    rent: tuple[float, str] | None = None,
) -> dict[str, str]:
    """Return a dict with the four required parts, derived deterministically
    from the clause text, its risk level, matched keywords, and any monetary
    figures rule-extracted from the clause itself."""

    kw_str = ", ".join(matched_keywords) if matched_keywords else ""
    summary = _summarise(clause_text)
    exposures = extract_clause_exposure(clause_text, rent)
    category = _categorise(clause_text, matched_keywords)

    # 1. Plain-language explanation
    if kw_str:
        explanation = f"In plain terms: this clause is about {kw_str}. {summary}"
    else:
        explanation = summary

    # 2. Why it matters — category-aware so two High-risk clauses about very
    # different things (e.g. a deposit vs. an arbitration clause) don't read
    # near-identically just because they share a risk level.
    why_it_matters = _pick_template(_WHY_TEMPLATES, risk_level, category)

    # 3. Potential financial impact
    if exposures:
        amounts_str = "; ".join(item["text"] for item in exposures)
        financial_impact = (
            f"Based on the figures stated here, this could realistically cost you "
            f"around {amounts_str}."
        )
    else:
        financial_impact = (
            "No specific amount is written into this clause, so the real cost "
            "depends on how it's applied — ask the other side for concrete figures "
            "before you sign."
        )

    # 4. Suggested action — likewise category-aware.
    suggested_action = _pick_template(_ACTION_TEMPLATES, risk_level, category)

    return {
        "explanation": explanation,
        "why_it_matters": why_it_matters,
        "financial_impact": financial_impact,
        "suggested_action": suggested_action,
    }


def merge_breakdown(base: dict[str, str], overlay: dict[str, str] | None) -> dict[str, str]:
    """Layer an (optional) AI-polished breakdown on top of the deterministic
    `base`. Only non-empty overlay values replace the base — so a partial or
    failed AI response still leaves every part populated."""
    if not overlay:
        return base
    merged = dict(base)
    for key in _BREAKDOWN_KEYS:
        value = overlay.get(key)
        if value:
            merged[key] = value
    return merged
