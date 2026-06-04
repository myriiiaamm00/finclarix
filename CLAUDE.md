# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FinClariX** — a Streamlit web app that helps young expats and students understand financial contracts (rental agreements, bank account terms, etc.) by analysing them with AI and explaining each clause in plain language, with risk levels (High / Medium / Low) and multilingual support.

Core user flow: upload a PDF or paste text → clauses are extracted and scanned for risky keywords → Claude explains each risky clause → user downloads a Markdown report.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py

# Copy env template and add your API key
cp .env.example .env
```

No test suite is configured yet. Add pytest tests under `tests/` when needed.

## Tech Stack

- **UI:** Streamlit (`app.py`)
- **PDF extraction:** pdfplumber (`src/pdf_reader.py`)
- **Risk detection:** keyword matching against `data/risk_keywords.json`
- **AI explanations:** Anthropic Claude API via `anthropic` SDK (`src/explanation_generator.py`)
- **Env vars:** `python-dotenv` loads `.env`; key used: `ANTHROPIC_API_KEY`

## Architecture

```
app.py                        ← Streamlit entry point; all UI state lives in st.session_state
src/
  pdf_reader.py               ← extract_text_from_pdf() + split_into_clauses()
  risk_detector.py            ← load_keywords() + detect_risks() per clause
  risk_scoring.py             ← score_clause() → "High" | "Medium" | "Low" | "Informational"
  explanation_generator.py    ← explain_clause() → calls Claude API with cached system prompt
  report_generator.py         ← generate_report() → returns Markdown string
data/
  risk_keywords.json          ← {"high": [...], "medium": [...], "low": [...]}
sample_contracts/             ← .txt files for testing via the Paste Text tab
```

**Analysis pipeline (in `app.py`):**
1. `split_into_clauses()` — regex splits on numbered sections, Articles, or double newlines
2. `detect_risks()` — substring match per clause against all keyword lists
3. `score_clause()` — highest-level keyword match wins; no match → Informational
4. `explain_clause()` — called only for High/Medium/Low clauses when AI is enabled; system prompt uses `cache_control: ephemeral` for prompt caching across the batch

**Risk keywords:** editing `data/risk_keywords.json` is the primary way to tune detection sensitivity — no code changes needed.
