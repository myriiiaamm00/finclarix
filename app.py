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
    initial_sidebar_state="expanded",
)

# ── Stylesheet ────────────────────────────────────────────────────────────────
_CSS = """
/* ── Reset ──────────────────────────────────────────────── */
* { box-sizing: border-box; }

/* ── Layout ──────────────────────────────────────────────── */
.block-container { max-width: 880px !important; padding: 1.5rem 2.5rem 5rem !important; }

/* ── Hide Streamlit chrome ───────────────────────────────── */
#MainMenu, footer, [data-testid="stDecoration"],
[data-testid="stToolbar"] { display: none !important; }

/* ── Brand header ────────────────────────────────────────── */
.brand-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 10px 0 6px;
}
.brand-name {
    font-size: 1.75rem;
    font-weight: 800;
    color: #F0F4FF;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin: 0;
}
.brand-tagline {
    font-size: 0.8rem;
    color: #3D5575;
    margin: 3px 0 0;
    letter-spacing: 0.1px;
}
.divider-line {
    height: 1px;
    background: linear-gradient(90deg, #162040 0%, transparent 100%);
    margin: 14px 0 22px;
}

/* ── Sidebar ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #080F20 !important;
    border-right: 1px solid #131F38;
}
.sidebar-section {
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    color: #2E4060 !important;
    margin: 22px 0 8px !important;
}
.how-it-works {
    padding-left: 16px;
    margin: 0;
    color: #4D6585;
    font-size: 0.8rem;
    line-height: 2.1;
}

/* ── Tabs ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: transparent;
    border-bottom: 1px solid #162040;
    margin-bottom: 18px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #435870 !important;
    font-weight: 500;
    font-size: 0.88rem;
    padding: 10px 20px;
    border-radius: 0;
    border-bottom: 2px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: #E0E8FF !important;
    border-bottom: 2px solid #4B7BF5 !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 4px; }

/* ── File uploader ───────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: #0A1424 !important;
    border: 1.5px dashed #1A3055 !important;
    border-radius: 10px !important;
    padding: 8px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #4B7BF5 !important;
}

/* ── Text area ───────────────────────────────────────────── */
.stTextArea textarea {
    background: #0A1424 !important;
    border: 1px solid #1A3055 !important;
    border-radius: 8px !important;
    color: #C8D6EC !important;
    font-size: 0.85rem !important;
    line-height: 1.65 !important;
}
.stTextArea textarea:focus {
    border-color: #4B7BF5 !important;
    box-shadow: 0 0 0 3px rgba(75,123,245,0.12) !important;
}

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #3B6EF0 0%, #6048E8 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    letter-spacing: 0.15px;
    padding: 0.65rem 1.5rem !important;
    color: #fff !important;
    transition: opacity 0.15s, transform 0.1s;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.92;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"]:active { transform: translateY(0); }

.stDownloadButton > button {
    background: #0A1424 !important;
    border: 1px solid #1E3A5F !important;
    border-radius: 8px !important;
    color: #8BAAD0 !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: border-color 0.15s, color 0.15s;
}
.stDownloadButton > button:hover {
    border-color: #4B7BF5 !important;
    color: #D0DFFF !important;
    background: #0D1A30 !important;
}

/* ── Selectbox & inputs ──────────────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"] > div > div > input {
    background: #0A1424 !important;
    border-color: #1A3055 !important;
    border-radius: 8px !important;
}

/* ── Alerts ──────────────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 8px !important; font-size: 0.85rem; }

/* ── Progress bar ────────────────────────────────────────── */
[data-testid="stProgressBar"] > div { background: #4B7BF5 !important; border-radius: 4px; }

/* ── Expander (PDF preview) ──────────────────────────────── */
[data-testid="stExpander"] {
    background: #0A1424 !important;
    border: 1px solid #162040 !important;
    border-radius: 8px !important;
}

/* ── Dashboard ───────────────────────────────────────────── */
.dashboard-heading {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #2E4060;
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
    background: #0A1424;
    border: 1px solid #131F38;
    border-radius: 12px;
    padding: 18px 14px 16px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 0 0 12px 12px;
}
.metric-high::after   { background: #EF4444; }
.metric-medium::after { background: #F59E0B; }
.metric-low::after    { background: #10B981; }
.metric-informational::after { background: #334155; }
.metric-number {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 7px;
    font-variant-numeric: tabular-nums;
}
.metric-num-high          { color: #EF4444; }
.metric-num-medium        { color: #F59E0B; }
.metric-num-low           { color: #10B981; }
.metric-num-informational { color: #3D5575; }
.metric-label {
    font-size: 0.7rem;
    color: #3D5575;
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
.section-high          { background: rgba(239,68,68,0.07);  color: #EF4444; border-left: 3px solid #EF4444; }
.section-medium        { background: rgba(245,158,11,0.07); color: #F59E0B; border-left: 3px solid #F59E0B; }
.section-low           { background: rgba(16,185,129,0.07); color: #10B981; border-left: 3px solid #10B981; }
.section-informational { background: rgba(51,65,85,0.15);   color: #475569; border-left: 3px solid #334155; }
.clause-count { font-weight: 400; opacity: 0.65; font-size: 0.78rem; }

/* ── Clause accordion cards ──────────────────────────────── */
details.clause-card {
    background: #0A1424;
    border: 1px solid #131F38;
    border-radius: 10px;
    margin-bottom: 8px;
    overflow: hidden;
    transition: border-color 0.15s, box-shadow 0.15s;
}
details.clause-card:hover         { border-color: #1E3560; box-shadow: 0 2px 20px rgba(0,0,0,0.3); }
details.clause-card[open]         { border-color: #1E3560; box-shadow: 0 4px 28px rgba(0,0,0,0.35); }
details.clause-high               { border-left: 3px solid #EF4444; }
details.clause-medium             { border-left: 3px solid #F59E0B; }
details.clause-low                { border-left: 3px solid #10B981; }
details.clause-informational      { border-left: 3px solid #253347; }

details.clause-card > summary {
    padding: 13px 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 11px;
    list-style: none;
    color: #A8BAD4;
    font-size: 0.86rem;
    user-select: none;
}
details.clause-card > summary::-webkit-details-marker { display: none; }
details.clause-card > summary::after {
    content: "›";
    margin-left: auto;
    font-size: 1.3rem;
    line-height: 1;
    color: #253347;
    transition: transform 0.2s;
    flex-shrink: 0;
}
details.clause-card[open] > summary::after { transform: rotate(90deg); color: #4B7BF5; }
details.clause-card > summary:hover { color: #D0DFF5; }

.clause-preview { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; flex: 1; min-width: 0; }

.clause-body { padding: 2px 16px 16px; border-top: 1px solid #0E1C30; }

.clause-meta-label {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #253347;
    margin: 14px 0 6px;
}
.clause-full-text {
    background: #060C19;
    border-left: 2px solid #152238;
    padding: 12px 14px;
    border-radius: 4px;
    color: #5C7A98;
    font-size: 0.82rem;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Keyword badges ──────────────────────────────────────── */
.keywords-row { margin: 12px 0 4px; display: flex; flex-wrap: wrap; gap: 5px; }
.kw-badge {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
}
.kw-high          { background: rgba(239,68,68,0.10);  color: #EF4444; border: 1px solid rgba(239,68,68,0.18); }
.kw-medium        { background: rgba(245,158,11,0.10); color: #F59E0B; border: 1px solid rgba(245,158,11,0.18); }
.kw-low           { background: rgba(16,185,129,0.10); color: #10B981; border: 1px solid rgba(16,185,129,0.18); }
.kw-informational { background: rgba(51,65,85,0.15);   color: #475569; border: 1px solid rgba(51,65,85,0.25); }

/* ── AI explanation box ──────────────────────────────────── */
.ai-box {
    background: linear-gradient(135deg, #080F1E 0%, #0B1525 100%);
    border: 1px solid #1A3050;
    border-radius: 8px;
    padding: 14px 16px;
    margin-top: 14px;
}
.ai-label {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #4B7BF5;
    margin-bottom: 8px;
}
.ai-box p {
    margin: 0;
    color: #8BACC8;
    font-size: 0.875rem;
    line-height: 1.7;
}

/* ── Risk level badge (inside summary) ───────────────────── */
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
.badge-high          { background: rgba(239,68,68,0.14);  color: #EF4444; }
.badge-medium        { background: rgba(245,158,11,0.14); color: #F59E0B; }
.badge-low           { background: rgba(16,185,129,0.14); color: #10B981; }
.badge-informational { background: rgba(51,65,85,0.20);   color: #475569; }

/* ── Scrollbar ───────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #070D1A; }
::-webkit-scrollbar-thumb { background: #1A2E4A; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #264570; }
"""

st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _logo_tag(width: int = 48) -> str:
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        r = max(4, width // 7)
        return (
            f'<img src="data:image/png;base64,{b64}" '
            f'width="{width}" height="{width}" '
            f'style="border-radius:{r}px;object-fit:contain;display:block;flex-shrink:0;" alt="">'
        )
    r = max(4, width // 7)
    fs = width // 2
    return (
        f'<div style="width:{width}px;height:{width}px;'
        f'background:linear-gradient(135deg,#3B6EF0,#6048E8);'
        f'border-radius:{r}px;display:flex;align-items:center;'
        f'justify-content:center;font-size:{fs}px;font-weight:900;'
        f'color:white;font-family:sans-serif;flex-shrink:0;letter-spacing:-1px;">F</div>'
    )


def _build_results_html(by_level: dict) -> str:
    counts = {lvl: len(by_level[lvl]) for lvl in RISK_LEVELS}

    metric_labels = {
        "High": "🔴 High Risk",
        "Medium": "🟡 Medium Risk",
        "Low": "🟢 Low Risk",
        "Informational": "ℹ️ Informational",
    }

    # Metrics grid
    metrics_html = '<div class="dashboard-heading">Risk Summary</div><div class="metrics-grid">'
    for lvl in RISK_LEVELS:
        lc = lvl.lower()
        metrics_html += (
            f'<div class="metric-card metric-{lc}">'
            f'<div class="metric-number metric-num-{lc}">{counts[lvl]}</div>'
            f'<div class="metric-label">{metric_labels[lvl]}</div>'
            f'</div>'
        )
    metrics_html += "</div>"

    sections_html = ""
    for lvl in RISK_LEVELS:
        group = by_level[lvl]
        if not group:
            continue

        lc = lvl.lower()
        emoji = RISK_EMOJI[lvl]
        n = len(group)
        plural = "s" if n != 1 else ""

        sections_html += (
            f'<div class="risk-section-header section-{lc}">'
            f'<span>{emoji} {lvl} Risk</span>'
            f'<span class="clause-count">{n} clause{plural}</span>'
            f'</div>'
        )

        for i, clause in enumerate(group, 1):
            text = clause["text"]
            preview = text[:100].replace("\n", " ")
            if len(text) > 100:
                preview += "…"

            kw_html = ""
            if clause["keywords"]:
                badges = "".join(
                    f'<span class="kw-badge kw-{lc}">{html_lib.escape(k)}</span>'
                    for k in clause["keywords"]
                )
                kw_html = (
                    f'<div class="clause-meta-label">Flagged terms</div>'
                    f'<div class="keywords-row">{badges}</div>'
                )

            ai_html = ""
            if clause.get("explanation"):
                expl = html_lib.escape(clause["explanation"]).replace("\n", "<br>")
                ai_html = (
                    f'<div class="ai-box">'
                    f'<div class="ai-label">✦ Plain talk</div>'
                    f'<p>{expl}</p>'
                    f'</div>'
                )

            sections_html += (
                f'<details class="clause-card clause-{lc}">'
                f'<summary>'
                f'<span class="badge-level badge-{lc}">{lvl.upper()}</span>'
                f'<span class="clause-preview">{html_lib.escape(preview)}</span>'
                f'</summary>'
                f'<div class="clause-body">'
                f'<div class="clause-meta-label">Full clause text</div>'
                f'<div class="clause-full-text">{html_lib.escape(text)}</div>'
                f'{kw_html}'
                f'{ai_html}'
                f'</div>'
                f'</details>'
            )

    return metrics_html + sections_html


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="brand-header">
        {_logo_tag(50)}
        <div>
            <div class="brand-name">FinClariX</div>
            <div class="brand-tagline">Finance that sticks, minus the tricks.</div>
        </div>
    </div>
    <div class="divider-line"></div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;
                    padding-bottom:16px;border-bottom:1px solid #131F38;margin-bottom:4px;">
            {_logo_tag(30)}
            <span style="font-weight:700;font-size:0.92rem;color:#D0DCEF;
                         letter-spacing:-0.2px;">FinClariX</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<p class="sidebar-section">Settings</p>', unsafe_allow_html=True)

    language = st.selectbox(
        "Explanation language",
        ["English", "French", "Spanish", "German", "Dutch", "Mandarin Chinese"],
        help="Language for AI-generated clause explanations.",
    )

    use_ai = st.toggle("Enable AI explanations", value=True)

    api_key_input = st.text_input(
        "Anthropic API key (optional)",
        type="password",
        placeholder="sk-ant-… or set ANTHROPIC_API_KEY",
        help="Overrides the ANTHROPIC_API_KEY environment variable for this session.",
    )
    if api_key_input:
        os.environ["ANTHROPIC_API_KEY"] = api_key_input

    if use_ai and not os.getenv("ANTHROPIC_API_KEY"):
        st.warning("No API key set — AI explanations will be skipped.")

    st.markdown('<p class="sidebar-section">How it works</p>', unsafe_allow_html=True)
    st.markdown(
        """
        <ol class="how-it-works">
            <li>Upload a PDF or paste contract text</li>
            <li>Clauses scanned for risky keywords</li>
            <li>Claude explains each risky clause</li>
            <li>Download your full Markdown report</li>
        </ol>
        """,
        unsafe_allow_html=True,
    )

# ── Input tabs ────────────────────────────────────────────────────────────────
tab_upload, tab_paste = st.tabs(["📎  Upload PDF", "📝  Paste Text"])

raw_text = ""
source_name = "contract"

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
            st.success(f"Text extracted from **{uploaded.name}**")
            with st.expander("Preview extracted text"):
                st.text(raw_text[:3000] + ("…" if len(raw_text) > 3000 else ""))
        else:
            st.warning(
                "No text found — this may be a scanned/image PDF. "
                "Try copying the text and using the Paste Text tab instead."
            )

with tab_paste:
    pasted = st.text_area(
        "Contract text",
        height=260,
        placeholder="Paste the full text of your contract here…",
        label_visibility="collapsed",
    )
    if pasted.strip():
        raw_text = pasted.strip()
        source_name = "pasted_contract"

# ── Analyse ───────────────────────────────────────────────────────────────────
if raw_text.strip():
    if st.button("🔍  Analyse Contract", type="primary", use_container_width=True):
        keywords_db = load_keywords()
        clauses = split_into_clauses(raw_text)

        if not clauses:
            st.error(
                "Could not detect any clauses. "
                "Try separating sections with blank lines."
            )
            st.stop()

        results: list[dict] = []
        ai_enabled = use_ai and bool(os.getenv("ANTHROPIC_API_KEY"))
        progress = st.progress(0, text="Scanning clauses…")

        for i, clause_text in enumerate(clauses):
            matches = detect_risks(clause_text, keywords_db)
            risk = score_clause(matches)
            kws = all_keywords(matches)

            explanation = ""
            if ai_enabled and risk != "Informational":
                try:
                    explanation = explain_clause(clause_text, risk, kws, language)
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

# ── Results dashboard ─────────────────────────────────────────────────────────
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
    st.download_button(
        label="⬇️  Download Markdown Report",
        data=report_md,
        file_name=f"finclarix_report_{safe_name}.md",
        mime="text/markdown",
        use_container_width=True,
    )
