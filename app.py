import base64
import html as html_lib
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.clause_breakdown import build_breakdown, merge_breakdown
from src.explanation_generator import explain_clause
from src.financial_extractor import build_exposure_summary, find_rent_amount
from src.free_translate import translate_text
from src.i18n import t
from src.pdf_reader import OCR_AVAILABLE, extract_text_from_pdf, split_into_clauses
from src.report_generator import generate_report_pdf
from src.risk_detector import detect_risks, load_keywords
from src.risk_scoring import RISK_EMOJI, RISK_LEVELS, all_keywords, score_clause

# ── Project paths (always resolved relative to this file, never hardcoded) ───
# This makes the app launch-location-independent: `streamlit run app.py` works
# the same whether you run it from the project root, a parent directory, or
# on a different machine/OS entirely.
BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "logo.png"
KEYWORDS_PATH = BASE_DIR / "data" / "risk_keywords.json"
SAMPLE_CONTRACTS_DIR = BASE_DIR / "sample_contracts"

# Reads ANTHROPIC_API_KEY (and any other settings) from a local .env file if
# present. Missing the file — or the key — is not an error: explain_clause()
# already degrades to the deterministic rule-based breakdown without it.
load_dotenv(BASE_DIR / ".env")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinClariX",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session state defaults ────────────────────────────────────────────────────
_LANGUAGES = [
    "English", "Spanish", "Chinese", "Dutch", "French", "German", "Italian",
    "Portuguese", "Polish", "Romanian", "Swedish", "Czech", "Hungarian", "Greek",
]

for _k, _v in [("settings_open", False), ("language", "English"), ("use_ai", True), ("api_key", "")]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Restore API key from session so it survives reruns
if st.session_state.api_key:
    os.environ["ANTHROPIC_API_KEY"] = st.session_state.api_key

# Read current settings (updated below if panel is open)
_lang = st.session_state.language
_use_ai = st.session_state.use_ai

# ── Stylesheet ────────────────────────────────────────────────────────────────
_CSS = """
/* ── Hide Streamlit chrome & sidebar ────────────────────── */
#MainMenu, footer, [data-testid="stDecoration"],
[data-testid="stToolbar"], section[data-testid="stSidebar"],
[data-testid="collapsedControl"] { display: none !important; }

/* ── Page ────────────────────────────────────────────────── */
.stApp, [data-testid="stAppViewContainer"],
[data-testid="stHeader"] { background: #EDE8DC !important; }
.block-container { padding: 0 2.5rem 5rem !important; max-width: 1100px !important; }

/* ── Header area ─────────────────────────────────────────── */
.page-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    padding: 32px 0 20px;
}
.logo-block { display: flex; flex-direction: column; align-items: flex-start; gap: 0; }
.brand-tagline {
    font-size: 0.82rem;
    color: #4A7C59;
    font-style: italic;
    margin: 8px 0 0;
    letter-spacing: 0.05px;
    text-align: center;
}
.divider-line {
    height: 1px;
    background: linear-gradient(90deg, #C8E0D0 0%, transparent 80%);
    margin: 0 0 28px;
}

/* ── Hamburger button ────────────────────────────────────── */
.menu-btn > div > button {
    background: transparent !important;
    border: 1.5px solid #C8E0D0 !important;
    border-radius: 8px !important;
    color: #4A7C59 !important;
    font-size: 1.15rem !important;
    font-weight: 400 !important;
    padding: 7px 14px !important;
    line-height: 1 !important;
    transition: background 0.15s, border-color 0.15s;
}
.menu-btn > div > button:hover {
    background: #E8F3EC !important;
    border-color: #4A7C59 !important;
}

/* ── Settings panel ──────────────────────────────────────── */
.settings-panel {
    background: #FFFFFF;
    border: 1px solid #C8E0D0;
    border-radius: 12px;
    padding: 20px 18px 24px;
    position: sticky;
    top: 16px;
}
.panel-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1.1px;
    text-transform: uppercase;
    color: #4A7C59;
    margin: 0 0 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #E4F0E8;
}
.panel-section {
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    color: #6B9E78 !important;
    margin: 20px 0 8px !important;
}
.how-it-works {
    padding-left: 16px;
    margin: 0;
    color: #6B9E78;
    font-size: 0.8rem;
    line-height: 2.1;
}

/* ── Tabs ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: transparent;
    border-bottom: 1px solid #C8E0D0;
    margin-bottom: 16px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #6B9E78 !important;
    font-weight: 500;
    font-size: 0.88rem;
    padding: 10px 20px;
    border-radius: 0;
    border-bottom: 2px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: #4A7C59 !important;
    border-bottom: 2px solid #4A7C59 !important;
    background: transparent !important;
}

/* ── File uploader ───────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: #F2F8F4 !important;
    border: 1.5px dashed #A8D4B4 !important;
    border-radius: 10px !important;
    padding: 8px !important;
}
[data-testid="stFileUploader"]:hover { border-color: #4A7C59 !important; }

/* ── Text area ───────────────────────────────────────────── */
.stTextArea textarea {
    background: #F2F8F4 !important;
    border: 1px solid #C8E0D0 !important;
    border-radius: 8px !important;
    color: #1A1A1A !important;
    font-size: 0.85rem !important;
    line-height: 1.65 !important;
}
.stTextArea textarea:focus {
    border-color: #4A7C59 !important;
    box-shadow: 0 0 0 3px rgba(74,124,89,0.12) !important;
}

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: #4A7C59 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    padding: 0.65rem 1.5rem !important;
    color: #FFFFFF !important;
    transition: background 0.15s, transform 0.1s;
}
.stButton > button[kind="primary"]:hover {
    background: #3D6B4A !important;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"]:active { transform: translateY(0); }

.stDownloadButton > button {
    background: #FFFFFF !important;
    border: 1.5px solid #C8E0D0 !important;
    border-radius: 8px !important;
    color: #4A7C59 !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: border-color 0.15s, background 0.15s;
}
.stDownloadButton > button:hover {
    border-color: #4A7C59 !important;
    background: #F2F8F4 !important;
}

/* ── Selectbox & inputs ──────────────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"] > div > div > input {
    background: #F2F8F4 !important;
    border-color: #C8E0D0 !important;
    border-radius: 8px !important;
    color: #1A1A1A !important;
}

/* ── Alerts ──────────────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 8px !important; font-size: 0.85rem; }

/* ── Progress bar ────────────────────────────────────────── */
[data-testid="stProgressBar"] > div { background: #4A7C59 !important; border-radius: 4px; }

/* ── Expander (PDF preview) ──────────────────────────────── */
[data-testid="stExpander"] {
    background: #F2F8F4 !important;
    border: 1px solid #C8E0D0 !important;
    border-radius: 8px !important;
}

/* ── Dashboard heading ───────────────────────────────────── */
.dashboard-heading {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #6B9E78;
    margin: 0 0 14px;
}

/* ── Metrics grid ────────────────────────────────────────── */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 32px;
}
.metric-card {
    background: #FFFFFF;
    border: 1px solid #C8E0D0;
    border-radius: 12px;
    padding: 18px 14px 16px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 6px rgba(74,124,89,0.07);
}
.metric-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 0 0 12px 12px;
}
.metric-high::after          { background: #DC2626; }
.metric-medium::after        { background: #D97706; }
.metric-low::after           { background: #4A7C59; }
.metric-informational::after { background: #A8D4B4; }
.metric-number {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 7px;
    font-variant-numeric: tabular-nums;
}
.metric-num-high          { color: #DC2626; }
.metric-num-medium        { color: #D97706; }
.metric-num-low           { color: #4A7C59; }
.metric-num-informational { color: #6B9E78; }
.metric-label {
    font-size: 0.7rem;
    color: #6B9E78;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.7px;
}

/* ── Risk section headers ────────────────────────────────── */
.risk-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 14px;
    border-radius: 7px;
    margin: 28px 0 10px;
    font-weight: 700;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
.section-high          { background: rgba(220,38,38,0.05);  color: #B91C1C; border-left: 3px solid #DC2626; }
.section-medium        { background: rgba(217,119,6,0.05);  color: #B45309; border-left: 3px solid #D97706; }
.section-low           { background: rgba(74,124,89,0.06);  color: #3D6B4A; border-left: 3px solid #4A7C59; }
.section-informational { background: rgba(74,124,89,0.04);  color: #6B9E78; border-left: 3px solid #A8D4B4; }
.clause-count { font-weight: 400; opacity: 0.65; font-size: 0.78rem; }

/* ── Clause accordion cards ──────────────────────────────── */
details.clause-card {
    background: #FFFFFF;
    border: 1px solid #C8E0D0;
    border-radius: 10px;
    margin-bottom: 8px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(74,124,89,0.06);
    transition: border-color 0.15s, box-shadow 0.15s;
}
details.clause-card:hover    { border-color: #8BBD9A; box-shadow: 0 3px 16px rgba(74,124,89,0.10); }
details.clause-card[open]    { border-color: #8BBD9A; box-shadow: 0 4px 20px rgba(74,124,89,0.12); }
details.clause-high          { border-left: 3px solid #DC2626; }
details.clause-medium        { border-left: 3px solid #D97706; }
details.clause-low           { border-left: 3px solid #4A7C59; }
details.clause-informational { border-left: 3px solid #A8D4B4; }

details.clause-card > summary {
    padding: 13px 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 11px;
    list-style: none;
    color: #2D4A35;
    font-size: 0.86rem;
    user-select: none;
}
details.clause-card > summary::-webkit-details-marker { display: none; }
details.clause-card > summary::after {
    content: "›";
    margin-left: auto;
    font-size: 1.3rem;
    line-height: 1;
    color: #A8D4B4;
    transition: transform 0.2s;
    flex-shrink: 0;
}
details.clause-card[open] > summary::after { transform: rotate(90deg); color: #4A7C59; }
details.clause-card > summary:hover { color: #1A1A1A; }

.clause-preview { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; flex: 1; min-width: 0; }
.clause-body    { padding: 2px 16px 16px; border-top: 1px solid #E4F0E8; }

.clause-meta-label {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #A8D4B4;
    margin: 14px 0 6px;
}
.clause-full-text {
    background: #F2F8F4;
    border-left: 2px solid #C8E0D0;
    padding: 12px 14px;
    border-radius: 4px;
    color: #3D5C45;
    font-size: 0.82rem;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Keyword badges ──────────────────────────────────────── */
.keywords-row { margin: 12px 0 4px; display: flex; flex-wrap: wrap; gap: 5px; }
.kw-badge     { display: inline-block; padding: 3px 9px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; }
.kw-high          { background: rgba(220,38,38,0.07);  color: #B91C1C; border: 1px solid rgba(220,38,38,0.15); }
.kw-medium        { background: rgba(217,119,6,0.07);  color: #B45309; border: 1px solid rgba(217,119,6,0.15); }
.kw-low           { background: rgba(74,124,89,0.08);  color: #3D6B4A; border: 1px solid rgba(74,124,89,0.15); }
.kw-informational { background: rgba(74,124,89,0.05);  color: #6B9E78; border: 1px solid rgba(74,124,89,0.12); }

/* ── AI explanation box ──────────────────────────────────── */
.ai-box {
    background: #F2F8F4;
    border: 1px solid #C8E0D0;
    border-left: 3px solid #4A7C59;
    border-radius: 8px;
    padding: 14px 16px;
    margin-top: 14px;
}
.ai-label {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #4A7C59;
    margin-bottom: 8px;
}
.ai-box p { margin: 0; color: #2D4A35; font-size: 0.875rem; line-height: 1.7; }
.ai-note  { margin-top: 10px; color: #8BAE96; font-size: 0.72rem; font-style: italic; }

/* ── Four-part clause breakdown ───────────────────────────── */
.breakdown-part + .breakdown-part { margin-top: 12px; }
.breakdown-part-label {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: #6B9E78;
    margin-bottom: 3px;
}

/* ── Financial exposure summary ───────────────────────────── */
.exposure-box {
    background: #FBF7EE;
    border: 1px solid #EAD9B8;
    border-left: 3px solid #C8973F;
    border-radius: 8px;
    padding: 16px 18px;
    margin: 18px 0 28px;
}
.exposure-title {
    font-size: 0.8rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: #9C7322;
    margin-bottom: 4px;
}
.exposure-subtitle { font-size: 0.78rem; color: #8A6A36; margin-bottom: 12px; }
.exposure-list { margin: 0; padding-left: 20px; }
.exposure-list li { color: #5C4421; font-size: 0.86rem; line-height: 1.9; }
.exposure-list li b { color: #9C7322; }

/* ── Risk level badge ────────────────────────────────────── */
.badge-level {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.7px;
    text-transform: uppercase;
    flex-shrink: 0;
}
.badge-high          { background: rgba(220,38,38,0.09);  color: #B91C1C; }
.badge-medium        { background: rgba(217,119,6,0.09);  color: #B45309; }
.badge-low           { background: rgba(74,124,89,0.09);  color: #3D6B4A; }
.badge-informational { background: rgba(74,124,89,0.06);  color: #6B9E78; }

/* ── Scrollbar ───────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #EDE8DC; }
::-webkit-scrollbar-thumb { background: #C8E0D0; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #8BBD9A; }
"""

st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _logo_tag(width: int = 56) -> str:
    if LOGO_PATH.exists():
        mtime = int(LOGO_PATH.stat().st_mtime)
        with open(LOGO_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return (
            f'<img src="data:image/png;base64,{b64}" width="{width}" '
            f'data-v="{mtime}" '
            f'style="display:block;object-fit:contain;margin:0 auto;" alt="FinClariX">'
        )
    fs = width // 2
    return (
        f'<div style="font-size:{fs}px;font-weight:900;color:#4A7C59;'
        f'line-height:1;font-family:sans-serif;text-align:center;">F</div>'
    )


# Translation-key mapping for the four breakdown parts — labels are looked up
# via t() at render time so they follow the active language selection.
_BREAKDOWN_LABEL_KEYS = (
    ("explanation", "label_explanation"),
    ("why_it_matters", "label_why"),
    ("financial_impact", "label_financial_impact"),
    ("suggested_action", "label_suggested_action"),
)

# Risk-level → translation-key mapping for metric cards, section headers, and
# clause badges, so every label follows the active language (see src/i18n.py).
_METRIC_KEYS = {"High": "metric_high", "Medium": "metric_medium", "Low": "metric_low", "Informational": "metric_informational"}
_SECTION_KEYS = {"High": "metric_high", "Medium": "metric_medium", "Low": "metric_low", "Informational": "section_informational"}
_BADGE_KEYS = {"High": "badge_high", "Medium": "badge_medium", "Low": "badge_low", "Informational": "badge_informational"}


def _build_exposure_summary_html(items: list[dict], lang: str = "English") -> str:
    if not items:
        return ""

    # Financial Exposure Summary lines (e.g. "€4,050 early termination penalty
    # based on three months of €1,350 rent") are composed English sentences,
    # just like the clause breakdowns — translate them with the same 0-cost
    # free layer, FRESH on every render, so a language switch updates them
    # immediately (see the matching comment in _build_results_html for why
    # this happens at render time rather than being baked in at analysis
    # time). Cached by (text, lang), so repeat renders stay fast.
    translation_failed = False
    row_items = []
    for item in items:
        text = item.get("text", "")
        if lang != "English":
            translated_text, ok = translate_text(text, lang)
            if not ok:
                translation_failed = True
            text = translated_text
        row_items.append(text)
    rows = "".join(f"<li>{html_lib.escape(text)}</li>" for text in row_items)

    note_html = ""
    if translation_failed:
        note_html = f'<div class="ai-note">{html_lib.escape(t("translation_unavailable_notice", lang))}</div>'

    return (
        '<div class="exposure-box">'
        f'<div class="exposure-title">💰 {t("exposure_title", lang)}</div>'
        f'<div class="exposure-subtitle">{t("exposure_subtitle", lang)}</div>'
        f'<ul class="exposure-list">{rows}</ul>'
        f'{note_html}'
        '</div>'
    )


def _build_results_html(by_level: dict, exposure_items: list[dict] | None = None, lang: str = "English") -> str:
    counts = {lvl: len(by_level[lvl]) for lvl in RISK_LEVELS}
    risk_emoji_prefix = {"High": "🔴", "Medium": "🟡", "Low": "🟢", "Informational": "ℹ️"}

    html = f'<div class="dashboard-heading">{t("risk_summary", lang)}</div><div class="metrics-grid">'
    for lvl in RISK_LEVELS:
        lc = lvl.lower()
        html += (
            f'<div class="metric-card metric-{lc}">'
            f'<div class="metric-number metric-num-{lc}">{counts[lvl]}</div>'
            f'<div class="metric-label">{risk_emoji_prefix[lvl]} {t(_METRIC_KEYS[lvl], lang)}</div>'
            f'</div>'
        )
    html += "</div>"

    # The Financial Exposure Summary is FinClariX's flagship "quantified
    # impact" feature (per the business plan), so it's surfaced immediately
    # after the headline Risk Summary metrics — before the user has to scroll
    # through every individual clause group to find it.
    html += _build_exposure_summary_html(exposure_items or [], lang)

    clause_word = t("clause_singular", lang)
    clauses_word = t("clause_plural", lang)

    for lvl in RISK_LEVELS:
        group = by_level[lvl]
        if not group:
            continue
        lc = lvl.lower()
        n = len(group)
        html += (
            f'<div class="risk-section-header section-{lc}">'
            f'<span>{RISK_EMOJI[lvl]} {t(_SECTION_KEYS[lvl], lang)}</span>'
            f'<span class="clause-count">{n} {clause_word if n == 1 else clauses_word}</span>'
            f'</div>'
        )
        for i, clause in enumerate(group, 1):
            text = clause["text"]
            preview = text[:100].replace("\n", " ") + ("…" if len(text) > 100 else "")

            kw_html = ""
            if clause["keywords"]:
                badges = "".join(
                    f'<span class="kw-badge kw-{lc}">{html_lib.escape(k)}</span>'
                    for k in clause["keywords"]
                )
                kw_html = (
                    f'<div class="clause-meta-label">{t("flagged_terms", lang)}</div>'
                    f'<div class="keywords-row">{badges}</div>'
                )

            ai_html = ""
            breakdown = clause.get("breakdown")
            if breakdown:
                # ── Resolve what to actually display, FRESH on every render ──
                # This runs every time Streamlit reruns the script — including
                # immediately after the user flips the language selector — so
                # switching languages always shows up-to-date wording without
                # needing to re-click "Analyse Contract". (Baking translated
                # text into `results` at analysis time would freeze it at
                # whatever language was selected back then — exactly the bug
                # this structure avoids.)
                display_breakdown = dict(breakdown)
                note_parts: list[str] = []

                if clause.get("localized_by_ai") and clause.get("ai_breakdown"):
                    # The (paid) Claude path already produced wording in the
                    # selected language for this clause — use it as-is, no
                    # machine translation needed (and no notice to show).
                    display_breakdown = merge_breakdown(display_breakdown, clause["ai_breakdown"])
                else:
                    note_key = clause.get("ai_note_key")
                    if note_key == "ai_disabled_notice":
                        # Intentionally silent — per user request, the
                        # "AI explanations are disabled (no API key set) …"
                        # notice is hidden entirely. The rule-based / machine-
                        # translated breakdown is still shown below as normal,
                        # just without the explanatory note about why it's
                        # not AI-generated.
                        pass
                    elif note_key == "ai_unavailable":
                        note_parts.append(
                            "AI wording unavailable for this clause — showing the rule-based breakdown."
                        )
                    elif note_key == "ai_error":
                        note_parts.append(
                            f"AI wording unavailable ({clause.get('ai_note_extra', '')}) — "
                            f"showing the rule-based breakdown."
                        )

                    # ── 0-cost dynamic mother-tongue translation ─────────────
                    # Whenever the selected display language isn't English and
                    # the breakdown above is still the deterministic ENGLISH
                    # baseline, machine-translate each of the four parts at
                    # render time via a FREE backend (see src/free_translate.py
                    # — defaults to the unofficial Google Translate endpoint;
                    # no API key needed; switchable to DeepL Free via the
                    # FINCLARIX_TRANSLATE_PROVIDER env var, no code changes).
                    # Results are cached by (text, lang), so repeated reruns —
                    # including every later language switch — stay fast.
                    #
                    # Any failure (rate limit, network error, …) keeps the
                    # English text and surfaces a small fallback notice,
                    # exactly mirroring the AI-unavailable notices above.
                    if lang != "English":
                        translated_parts = {}
                        translation_failed = False
                        for key, _label_key in _BREAKDOWN_LABEL_KEYS:
                            original = display_breakdown.get(key, "")
                            if original:
                                translated_text, ok = translate_text(original, lang)
                                translated_parts[key] = translated_text
                                if not ok:
                                    translation_failed = True
                        display_breakdown = {**display_breakdown, **translated_parts}
                        if translation_failed:
                            note_parts.append(t("translation_unavailable_notice", lang))

                parts_html = ""
                for key, label_key in _BREAKDOWN_LABEL_KEYS:
                    value = display_breakdown.get(key)
                    if not value:
                        continue
                    safe = html_lib.escape(value).replace("\n", "<br>")
                    parts_html += (
                        f'<div class="breakdown-part">'
                        f'<div class="breakdown-part-label">{t(label_key, lang)}</div>'
                        f'<p>{safe}</p></div>'
                    )
                note_html = ""
                if note_parts:
                    note_html = f'<div class="ai-note">{html_lib.escape(" ".join(note_parts))}</div>'
                ai_html = (
                    f'<div class="ai-box"><div class="ai-label">✦ {t("plain_talk", lang)}</div>'
                    f'{parts_html}{note_html}</div>'
                )

            html += (
                f'<details class="clause-card clause-{lc}">'
                f'<summary>'
                f'<span class="badge-level badge-{lc}">{t(_BADGE_KEYS[lvl], lang)}</span>'
                f'<span class="clause-preview">{html_lib.escape(preview)}</span>'
                f'</summary>'
                f'<div class="clause-body">'
                f'<div class="clause-meta-label">{t("full_clause_text", lang)}</div>'
                f'<div class="clause-full-text">{html_lib.escape(text)}</div>'
                f'{kw_html}{ai_html}'
                f'</div></details>'
            )

    return html


# ── Header row ────────────────────────────────────────────────────────────────
hdr_left, hdr_center, hdr_right = st.columns([1, 8, 1])

with hdr_left:
    st.markdown('<div class="menu-btn" style="padding-top:44px;">', unsafe_allow_html=True)
    if st.button("☰", key="toggle_settings"):
        st.session_state.settings_open = not st.session_state.settings_open
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with hdr_center:
    st.markdown(
        f"""
        <div style="padding-top:40px;text-align:center;">
            {_logo_tag(300)}
            <p class="brand-tagline">Finance that sticks, minus the tricks.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)

# ── Layout: optional left settings panel + main content ──────────────────────
if st.session_state.settings_open:
    panel_col, main_col = st.columns([1, 3], gap="large")
else:
    main_col = st.container()
    panel_col = None

# ── Settings panel (rendered first so API key is set before analysis) ─────────
if panel_col:
    with panel_col:
        st.markdown('<div class="settings-panel">', unsafe_allow_html=True)
        st.markdown(f'<div class="panel-title">⚙ {t("settings_title", _lang)}</div>', unsafe_allow_html=True)

        # NOTE: the selectbox label/options below are translated using the
        # CURRENT `_lang` (== st.session_state.language, read before this
        # panel runs) — i.e. the panel chrome reflects whatever language was
        # active when the page loaded. As soon as the user picks a new
        # language and the app reruns, every label (including this one)
        # re-renders in the newly selected language.
        new_lang = st.selectbox(
            t("language_label", _lang),
            _LANGUAGES,
            index=_LANGUAGES.index(st.session_state.language),
        )
        st.session_state.language = new_lang
        _lang = new_lang

        new_use_ai = st.toggle(t("enable_ai_label", _lang), value=st.session_state.use_ai)
        st.session_state.use_ai = new_use_ai
        _use_ai = new_use_ai

        # NOTE: the "Anthropic API key" text input, the "No API key — AI
        # explanations disabled" notice, and the "How it works" steps list
        # are intentionally NOT rendered in the sidebar (per user request —
        # keeps the panel focused on language/AI-toggle controls only).
        # The app still reads the key from `st.session_state.api_key` /
        # the `ANTHROPIC_API_KEY` environment variable (e.g. via `.env`),
        # so AI explanations keep working exactly as before for anyone who
        # sets the key that way — only the on-screen input/notice/steps
        # are hidden.

        st.markdown("</div>", unsafe_allow_html=True)

# ── Main content ──────────────────────────────────────────────────────────────
with main_col:
    # Input section centred at ~50% width
    raw_text = ""
    source_name = "contract"

    _, center_col, _ = st.columns([1, 2, 1])

    with center_col:
        tab_upload, tab_paste = st.tabs([
            f"📎  {t('tab_upload', _lang)}",
            f"📝  {t('tab_paste', _lang)}",
        ])

        with tab_upload:
            uploaded = st.file_uploader(
                "Upload contract PDF",
                type=["pdf"],
                label_visibility="collapsed",
                help=(
                    "Scanned/image-only PDFs are OCR'd automatically as a fallback."
                    if OCR_AVAILABLE else
                    "Scanned image PDFs without embedded text cannot be parsed "
                    "(install pytesseract + Tesseract to enable OCR)."
                ),
            )
            if uploaded:
                source_name = uploaded.name
                with st.spinner("Extracting text from PDF…"):
                    try:
                        raw_text = extract_text_from_pdf(uploaded)
                    except Exception as e:
                        st.error(f"Could not read PDF: {e}")
                if raw_text.strip():
                    st.success(f"Extracted **{uploaded.name}**")
                    with st.expander("Preview extracted text"):
                        st.text(raw_text[:3000] + ("…" if len(raw_text) > 3000 else ""))
                else:
                    st.warning("No text found — try the Paste Text tab instead.")

        with tab_paste:
            pasted = st.text_area(
                "Contract text",
                height=240,
                placeholder="Paste the full text of your contract here…",
                label_visibility="collapsed",
            )
            if pasted.strip():
                raw_text = pasted.strip()
                source_name = "pasted_contract"

    # Analyse button — same centred width
    if raw_text.strip():
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            if st.button(f"🔍  {t('analyse_button', _lang)}", type="primary", use_container_width=True):
                keywords_db = load_keywords(KEYWORDS_PATH)
                clauses = split_into_clauses(raw_text)

                if not clauses:
                    st.error("Could not detect clauses — try separating sections with blank lines.")
                    st.stop()

                results: list[dict] = []
                ai_enabled = _use_ai and bool(os.getenv("ANTHROPIC_API_KEY"))
                progress = st.progress(0, text="Scanning clauses…")

                # Deterministic, rule-based pass: locate the recurring monthly
                # rent figure once so per-clause exposures (termination,
                # renewal, …) can be derived from it.
                rent = find_rent_amount(clauses)

                for i, clause_text in enumerate(clauses):
                    matches = detect_risks(clause_text, keywords_db)
                    risk = score_clause(matches)
                    kws = all_keywords(matches)

                    # Deterministic four-part breakdown — always computed, so
                    # the app works fully without an API key. This is the
                    # LANGUAGE-INDEPENDENT baseline: we deliberately store it
                    # (plus a few status flags below) rather than any
                    # already-rendered, language-specific text. Baking
                    # translated strings or notices into `results` here would
                    # freeze them at whatever language was selected at
                    # analysis time — switching the language afterwards would
                    # then have no effect until the user re-clicked "Analyse
                    # Contract". Instead, the actual translation/notice text
                    # is resolved fresh on every render in _build_results_html
                    # (see the comments there), based on whatever `_lang` is
                    # *right now* — so flipping the language selector updates
                    # every explanation immediately, exactly as required.
                    breakdown = build_breakdown(clause_text, risk, kws, rent)
                    ai_breakdown_overlay = None
                    ai_note_key = None      # i18n key for a translatable notice
                    ai_note_extra = ""      # extra (English) detail, e.g. an exception message
                    localized_by_ai = False

                    if risk != "Informational":
                        if ai_enabled:
                            try:
                                ai_breakdown = explain_clause(clause_text, risk, kws, _lang)
                                if ai_breakdown is not None:
                                    # The (paid) Claude path already produced
                                    # wording in the selected language — store
                                    # it as an overlay so render-time merging
                                    # (and skipping machine translation) still
                                    # works correctly even after a later
                                    # language switch re-renders this clause.
                                    ai_breakdown_overlay = ai_breakdown
                                    localized_by_ai = True
                                else:
                                    ai_note_key = "ai_unavailable"
                            except Exception as e:
                                ai_note_key = "ai_error"
                                ai_note_extra = str(e)
                        elif not os.getenv("ANTHROPIC_API_KEY"):
                            # No API key configured at all — make that explicit
                            # on every risky clause. The actual (translated)
                            # notice text is resolved at render time via
                            # t("ai_disabled_notice", <current lang>).
                            ai_note_key = "ai_disabled_notice"

                    results.append(
                        {
                            "text": clause_text,
                            "risk": risk,
                            "keywords": kws,
                            "breakdown": breakdown,
                            "ai_breakdown": ai_breakdown_overlay,
                            "localized_by_ai": localized_by_ai,
                            "ai_note_key": ai_note_key,
                            "ai_note_extra": ai_note_extra,
                        }
                    )
                    progress.progress(
                        (i + 1) / len(clauses),
                        text=f"Scanning clause {i + 1} / {len(clauses)}…",
                    )

                progress.empty()
                st.session_state["results"] = results
                st.session_state["source_name"] = source_name
                # Stored as plain English — see _build_exposure_summary_html,
                # which translates these lines fresh on every render for the
                # same "language switch updates everything immediately" reason.
                st.session_state["exposure_items"] = build_exposure_summary(clauses)
                st.rerun()

    # Results — full width of main_col
    if "results" in st.session_state:
        results: list[dict] = st.session_state["results"]
        source_name = st.session_state.get("source_name", "contract")

        by_level: dict[str, list[dict]] = {lvl: [] for lvl in RISK_LEVELS}
        for r in results:
            by_level[r["risk"]].append(r)

        exposure_items = st.session_state.get("exposure_items", [])

        st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)
        st.markdown(_build_results_html(by_level, exposure_items, _lang), unsafe_allow_html=True)
        st.markdown('<div class="divider-line" style="margin-top:32px;"></div>', unsafe_allow_html=True)

        # Build the PDF breakdown in the selected language — same logic as
        # _build_results_html: AI overlay if available (already localised),
        # otherwise machine-translate the English baseline on the fly.
        # translate_text() results are cached, so any clause already rendered
        # on screen is free; only a fresh download with a new language pays
        # the network round-trip.
        def _pdf_breakdown(clause: dict) -> dict:
            bd = dict(clause["breakdown"])
            if clause.get("localized_by_ai") and clause.get("ai_breakdown"):
                bd = merge_breakdown(bd, clause["ai_breakdown"])
            elif _lang != "English":
                for key in ("explanation", "why_it_matters", "financial_impact", "suggested_action"):
                    if bd.get(key):
                        translated, _ = translate_text(bd[key], _lang)
                        bd[key] = translated
            return bd

        report_results = [{**r, "breakdown": _pdf_breakdown(r)} for r in results]

        # Translate exposure item text to match the selected language.
        pdf_exposure = exposure_items
        if _lang != "English" and exposure_items:
            pdf_exposure = []
            for item in exposure_items:
                translated_text, _ = translate_text(item["text"], _lang)
                pdf_exposure.append({**item, "text": translated_text})

        report_pdf = generate_report_pdf(report_results, source_name, pdf_exposure, lang=_lang)
        safe_name = source_name.replace(".pdf", "").replace(" ", "_")
        _, dl_col, _ = st.columns([1, 2, 1])
        with dl_col:
            st.download_button(
                label=f"⬇️  {t('download_report', _lang)}",
                data=report_pdf,
                file_name=f"finclarix_report_{safe_name}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
