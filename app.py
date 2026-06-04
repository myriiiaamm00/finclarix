import os

import streamlit as st
from dotenv import load_dotenv

from src.explanation_generator import explain_clause
from src.pdf_reader import extract_text_from_pdf, split_into_clauses
from src.report_generator import generate_report
from src.risk_detector import detect_risks, load_keywords
from src.risk_scoring import RISK_COLOR, RISK_EMOJI, RISK_LEVELS, all_keywords, score_clause

load_dotenv()

st.set_page_config(page_title="FinClariX", page_icon="📋", layout="wide")

st.markdown(
    """
    <style>
    .risk-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        color: white;
    }
    .stExpander { border-left: 3px solid #e0e0e0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("## 📋")
with col_title:
    st.markdown("## FinClariX")
    st.caption("Finance that sticks, minus the tricks.")

st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    language = st.selectbox(
        "Explanation language",
        ["English", "French", "Spanish", "German", "Dutch", "Mandarin Chinese"],
        help="Language for AI-generated explanations.",
    )

    use_ai = st.toggle("Enable AI explanations", value=True)

    api_key_input = st.text_input(
        "Anthropic API key (optional)",
        type="password",
        placeholder="sk-ant-… (or set ANTHROPIC_API_KEY)",
        help="Overrides the environment variable for this session.",
    )
    if api_key_input:
        os.environ["ANTHROPIC_API_KEY"] = api_key_input

    if use_ai and not os.getenv("ANTHROPIC_API_KEY"):
        st.warning("No API key found. AI explanations will be skipped.")

    st.divider()
    st.caption("**How it works**")
    st.caption("1. Upload a PDF or paste contract text")
    st.caption("2. Clauses are scanned for risky keywords")
    st.caption("3. Claude explains each risky clause in plain language")
    st.caption("4. Download a full Markdown report")

# ── Input ─────────────────────────────────────────────────────────────────────
tab_upload, tab_paste = st.tabs(["📎 Upload PDF", "📝 Paste Text"])

raw_text = ""
source_name = "contract"

with tab_upload:
    uploaded = st.file_uploader(
        "Upload a contract PDF",
        type=["pdf"],
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
            st.warning("No text found — this may be a scanned/image PDF. Try pasting the text instead.")

with tab_paste:
    pasted = st.text_area(
        "Paste contract text here",
        height=260,
        placeholder="Paste the full text of your contract…",
    )
    if pasted.strip():
        raw_text = pasted.strip()
        source_name = "pasted_contract"

# ── Analyse button ────────────────────────────────────────────────────────────
can_analyse = bool(raw_text.strip())

if can_analyse:
    if st.button("🔍 Analyse Contract", type="primary", use_container_width=True):
        keywords_db = load_keywords()
        clauses = split_into_clauses(raw_text)

        if not clauses:
            st.error("Could not detect any clauses in the provided text. Try splitting the text with blank lines between sections.")
            st.stop()

        results: list[dict] = []
        ai_enabled = use_ai and bool(os.getenv("ANTHROPIC_API_KEY"))

        progress = st.progress(0, text="Analysing clauses…")

        for i, clause_text in enumerate(clauses):
            matches = detect_risks(clause_text, keywords_db)
            risk = score_clause(matches)
            kws = all_keywords(matches)

            explanation = ""
            if ai_enabled and risk != "Informational":
                try:
                    explanation = explain_clause(clause_text, risk, kws, language)
                except Exception as e:
                    explanation = f"_Could not generate explanation: {e}_"

            results.append(
                {
                    "text": clause_text,
                    "risk": risk,
                    "keywords": kws,
                    "explanation": explanation,
                }
            )
            progress.progress(
                (i + 1) / len(clauses),
                text=f"Analysing clause {i + 1} / {len(clauses)}…",
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

    st.divider()
    st.subheader("📊 Risk Dashboard")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔴 High Risk", len(by_level["High"]))
    c2.metric("🟡 Medium Risk", len(by_level["Medium"]))
    c3.metric("🟢 Low Risk", len(by_level["Low"]))
    c4.metric("ℹ️ Informational", len(by_level["Informational"]))

    st.divider()

    for level in ("High", "Medium", "Low", "Informational"):
        group = by_level[level]
        if not group:
            continue

        emoji = RISK_EMOJI[level]
        color = RISK_COLOR[level]
        st.markdown(f"### {emoji} {level} Risk &nbsp; <span style='font-size:0.8rem;color:{color};'>({len(group)} clause{'s' if len(group) != 1 else ''})</span>", unsafe_allow_html=True)

        for i, clause in enumerate(group, 1):
            header = clause["text"][:90].replace("\n", " ") + ("…" if len(clause["text"]) > 90 else "")
            with st.expander(f"Clause {i}: {header}"):
                st.markdown("**Full clause text:**")
                st.info(clause["text"])

                if clause["keywords"]:
                    badge_html = " ".join(
                        f'<span class="risk-badge" style="background:{color};">{kw}</span>'
                        for kw in clause["keywords"]
                    )
                    st.markdown(f"**Flagged terms:** {badge_html}", unsafe_allow_html=True)

                if clause["explanation"]:
                    st.markdown("**Plain-language explanation:**")
                    st.success(clause["explanation"])
                elif level != "Informational" and not use_ai:
                    st.caption("_Enable AI explanations in the sidebar to get a plain-language summary._")

        st.markdown("")

    # ── Download report ───────────────────────────────────────────────────────
    st.divider()
    report_md = generate_report(results, source_name)
    safe_name = source_name.replace(".pdf", "").replace(" ", "_")
    st.download_button(
        label="⬇️ Download Markdown Report",
        data=report_md,
        file_name=f"finclarix_report_{safe_name}.md",
        mime="text/markdown",
        use_container_width=True,
    )
