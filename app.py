import base64
import html as html_lib
import os

import streamlit as st
from dotenv import load_dotenv

from src.explanation_generator import explain_clause
from src.pdf_reader import extract_text_from_pdf, split_into_clauses
from src.report_generator import generate_report
from src.risk_detector import detect_risks, load_keywords
from src.risk_scoring import RISK_EMOJI, RISK_LEVELS, all_keywords, score_clause

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinClariX",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session state defaults ────────────────────────────────────────────────────
_LANGUAGES = ["English", "French", "Spanish", "German", "Dutch", "Mandarin Chinese"]

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
[data-testid="stHeader"] { background: #FFFFFF !important; }
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
    margin: 6px 0 0;
    letter-spacing: 0.05px;
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
::-webkit-scrollbar-track { background: #FFFFFF; }
::-webkit-scrollbar-thumb { background: #C8E0D0; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #8BBD9A; }
"""

st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _logo_tag(width: int = 56) -> str:
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return (
            f'<img src="data:image/png;base64,{b64}" width="{width}" '
            f'style="display:block;object-fit:contain;" alt="FinClariX">'
        )
    fs = width // 2
    return (
        f'<div style="font-size:{fs}px;font-weight:900;color:#4A7C59;'
        f'line-height:1;font-family:sans-serif;">F</div>'
    )


def _build_results_html(by_level: dict) -> str:
    counts = {lvl: len(by_level[lvl]) for lvl in RISK_LEVELS}
    metric_labels = {
        "High": "🔴 High Risk", "Medium": "🟡 Medium Risk",
        "Low": "🟢 Low Risk",   "Informational": "ℹ️ Informational",
    }

    html = '<div class="dashboard-heading">Risk Summary</div><div class="metrics-grid">'
    for lvl in RISK_LEVELS:
        lc = lvl.lower()
        html += (
            f'<div class="metric-card metric-{lc}">'
            f'<div class="metric-number metric-num-{lc}">{counts[lvl]}</div>'
            f'<div class="metric-label">{metric_labels[lvl]}</div>'
            f'</div>'
        )
    html += "</div>"

    for lvl in RISK_LEVELS:
        group = by_level[lvl]
        if not group:
            continue
        lc = lvl.lower()
        n = len(group)
        html += (
            f'<div class="risk-section-header section-{lc}">'
            f'<span>{RISK_EMOJI[lvl]} {lvl} Risk</span>'
            f'<span class="clause-count">{n} clause{"s" if n != 1 else ""}</span>'
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
                kw_html = f'<div class="clause-meta-label">Flagged terms</div><div class="keywords-row">{badges}</div>'

            ai_html = ""
            if clause.get("explanation"):
                expl = html_lib.escape(clause["explanation"]).replace("\n", "<br>")
                ai_html = (
                    f'<div class="ai-box"><div class="ai-label">✦ Plain talk</div>'
                    f'<p>{expl}</p></div>'
                )

            html += (
                f'<details class="clause-card clause-{lc}">'
                f'<summary>'
                f'<span class="badge-level badge-{lc}">{lvl.upper()}</span>'
                f'<span class="clause-preview">{html_lib.escape(preview)}</span>'
                f'</summary>'
                f'<div class="clause-body">'
                f'<div class="clause-meta-label">Full clause text</div>'
                f'<div class="clause-full-text">{html_lib.escape(text)}</div>'
                f'{kw_html}{ai_html}'
                f'</div></details>'
            )

    return html


# ── Header row ────────────────────────────────────────────────────────────────
hdr_left, hdr_right = st.columns([14, 1])

with hdr_left:
    st.markdown(
        f"""
        <div style="padding-top:32px;">
            {_logo_tag(60)}
            <p class="brand-tagline">Finance that sticks, minus the tricks.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with hdr_right:
    st.markdown('<div class="menu-btn" style="padding-top:36px;text-align:right;">', unsafe_allow_html=True)
    if st.button("☰", key="toggle_settings"):
        st.session_state.settings_open = not st.session_state.settings_open
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)

# ── Layout: main content + optional right settings panel ─────────────────────
if st.session_state.settings_open:
    main_col, panel_col = st.columns([3, 1], gap="large")
else:
    main_col = st.container()
    panel_col = None

# ── Settings panel (rendered first so API key is set before analysis) ─────────
if panel_col:
    with panel_col:
        st.markdown('<div class="settings-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">⚙ Settings</div>', unsafe_allow_html=True)

        new_lang = st.selectbox(
            "Language",
            _LANGUAGES,
            index=_LANGUAGES.index(st.session_state.language),
        )
        st.session_state.language = new_lang
        _lang = new_lang

        new_use_ai = st.toggle("Enable AI explanations", value=st.session_state.use_ai)
        st.session_state.use_ai = new_use_ai
        _use_ai = new_use_ai

        new_key = st.text_input(
            "Anthropic API key",
            type="password",
            placeholder="sk-ant-… or set env var",
            help="Stored for this session only.",
        )
        if new_key:
            st.session_state.api_key = new_key
            os.environ["ANTHROPIC_API_KEY"] = new_key

        if _use_ai and not os.getenv("ANTHROPIC_API_KEY"):
            st.warning("No API key — AI explanations disabled.")

        st.markdown('<div class="panel-section">How it works</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <ol class="how-it-works">
                <li>Upload a PDF or paste text</li>
                <li>Clauses scanned for keywords</li>
                <li>Claude explains each clause</li>
                <li>Download your report</li>
            </ol>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

# ── Main content ──────────────────────────────────────────────────────────────
with main_col:
    # Input section centred at ~50% width
    raw_text = ""
    source_name = "contract"

    _, center_col, _ = st.columns([1, 2, 1])

    with center_col:
        tab_upload, tab_paste = st.tabs(["📎  Upload PDF", "📝  Paste Text"])

        with tab_upload:
            uploaded = st.file_uploader(
                "Upload contract PDF",
                type=["pdf"],
                label_visibility="collapsed",
                help="Scanned image PDFs without embedded text cannot be parsed.",
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
            if st.button("🔍  Analyse Contract", type="primary", use_container_width=True):
                keywords_db = load_keywords()
                clauses = split_into_clauses(raw_text)

                if not clauses:
                    st.error("Could not detect clauses — try separating sections with blank lines.")
                    st.stop()

                results: list[dict] = []
                ai_enabled = _use_ai and bool(os.getenv("ANTHROPIC_API_KEY"))
                progress = st.progress(0, text="Scanning clauses…")

                for i, clause_text in enumerate(clauses):
                    matches = detect_risks(clause_text, keywords_db)
                    risk = score_clause(matches)
                    kws = all_keywords(matches)

                    explanation = ""
                    if ai_enabled and risk != "Informational":
                        try:
                            explanation = explain_clause(clause_text, risk, kws, _lang)
                        except Exception as e:
                            explanation = f"Could not generate explanation: {e}"

                    results.append(
                        {"text": clause_text, "risk": risk, "keywords": kws, "explanation": explanation}
                    )
                    progress.progress(
                        (i + 1) / len(clauses),
                        text=f"Scanning clause {i + 1} / {len(clauses)}…",
                    )

                progress.empty()
                st.session_state["results"] = results
                st.session_state["source_name"] = source_name
                st.rerun()

    # Results — full width of main_col
    if "results" in st.session_state:
        results: list[dict] = st.session_state["results"]
        source_name = st.session_state.get("source_name", "contract")

        by_level: dict[str, list[dict]] = {lvl: [] for lvl in RISK_LEVELS}
        for r in results:
            by_level[r["risk"]].append(r)

        st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)
        st.markdown(_build_results_html(by_level), unsafe_allow_html=True)
        st.markdown('<div class="divider-line" style="margin-top:32px;"></div>', unsafe_allow_html=True)

        report_md = generate_report(results, source_name)
        safe_name = source_name.replace(".pdf", "").replace(" ", "_")
        _, dl_col, _ = st.columns([1, 2, 1])
        with dl_col:
            st.download_button(
                label="⬇️  Download Markdown Report",
                data=report_md,
                file_name=f"finclarix_report_{safe_name}.md",
                mime="text/markdown",
                use_container_width=True,
            )
