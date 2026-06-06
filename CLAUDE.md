# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FinClariX** — a Streamlit web app that helps young expats and students understand financial contracts (rental agreements, bank account terms, etc.) by analysing them clause-by-clause, classifying each one's risk level (High / Medium / Low / Informational), explaining it in plain language, and quantifying its potential financial impact — with a fully multilingual interface (14 languages) that works with or without an Anthropic API key.

Core user flow: upload a PDF or paste text → clauses are extracted and scanned for risky keywords → each risky clause gets a deterministic four-part breakdown (optionally polished/localised by Claude when AI is enabled) → a Financial Exposure Summary quantifies the contract's biggest costs → the user can switch the display language at any time (everything re-renders instantly) → the user downloads a PDF report.

**Guiding philosophy — deterministic baseline first, AI/translation as enhancement only:** every feature must work completely with zero API keys and zero recurring cost. AI (Claude) and machine translation only ever *layer on top* of a working rule-based baseline; they never gate core functionality. Keep this invariant intact when modifying any part of the pipeline.

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
- **PDF extraction:** pdfplumber, with optional OCR fallback via `pytesseract` + Tesseract (`src/pdf_reader.py`)
- **Risk detection:** keyword matching against `data/risk_keywords.json` (`src/risk_detector.py`, `src/risk_scoring.py`)
- **Deterministic clause breakdown:** topic-aware rule-based templates, no AI required (`src/clause_breakdown.py`)
- **Financial exposure extraction:** regex + arithmetic over stated amounts/time periods (`src/financial_extractor.py`)
- **AI explanations (optional):** Anthropic Claude API via `anthropic` SDK, localises + polishes the deterministic baseline (`src/explanation_generator.py`)
- **Static UI translation:** custom i18n lookup table covering 14 languages (`src/i18n.py`)
- **Dynamic translation fallback (optional, free):** runtime machine translation via stdlib-only HTTP calls — Google Translate Free (default) or DeepL Free (`src/free_translate.py`)
- **PDF report generation:** `fpdf2` — pure-Python, MIT/LGPL, no system dependencies (`src/report_generator.py`)
- **Env vars:** `python-dotenv` loads `.env`; primary key: `ANTHROPIC_API_KEY`; optional translation config: `FINCLARIX_TRANSLATE_PROVIDER`, `DEEPL_API_KEY`

## Architecture

```
app.py                        ← Streamlit entry point; all UI state lives in st.session_state
src/
  pdf_reader.py               ← extract_text_from_pdf() [+ _ocr_fallback()] and split_into_clauses()
  risk_detector.py            ← load_keywords() + detect_risks() per clause
  risk_scoring.py             ← score_clause() → "High" | "Medium" | "Low" | "Informational"
  clause_breakdown.py         ← build_breakdown() / merge_breakdown() → deterministic 4-part explanation (no AI)
  financial_extractor.py      ← find_rent_amount(), build_exposure_summary(), extract_clause_exposure()
  explanation_generator.py    ← explain_clause() → optional AI-polished, localised rewrite via Claude
  free_translate.py           ← translate_text() → free runtime machine-translation fallback (cached)
  i18n.py                     ← t(key, lang) → static UI-chrome translations across 14 languages
  report_generator.py         ← generate_report_pdf() → polished, downloadable PDF report (fpdf2)
data/
  risk_keywords.json          ← {"high": [...], "medium": [...], "low": [...]}
sample_contracts/             ← .txt files for testing via the Paste Text tab
```

## Analysis Pipeline (in `app.py`, "Analyse Contract" handler)

1. `split_into_clauses()` — regex splits on numbered sections, Articles, or double newlines. If the uploaded PDF has no embedded text layer, `extract_text_from_pdf()` transparently falls back to `_ocr_fallback()` (Tesseract OCR via `pytesseract`) first — see *OCR fallback* below.
2. `detect_risks()` — substring match per clause against all keyword lists in `data/risk_keywords.json`.
3. `score_clause()` — highest-level keyword match wins; no match → `Informational`.
4. `build_breakdown()` (`src/clause_breakdown.py`) — produces the deterministic four-part explanation (*Plain-language explanation / Why it matters / Potential financial impact / Suggested action*) for every risky clause, using topic-aware templates (`_CATEGORY_RULES`: deposit, renewal/termination, liability/arbitration, fees/charges, notice/utilities, default). **Always runs**, with or without an API key — this is the baseline the rest of the pipeline degrades to.
5. `build_exposure_summary()` / `find_rent_amount()` (`src/financial_extractor.py`) — independently scans the whole contract for stated amounts and time periods and computes concrete projected costs (e.g. "three months of €1,350 rent = €4,050"). Fully deterministic, runs once per analysis, stored in `st.session_state["exposure_items"]`.
6. `explain_clause()` (`src/explanation_generator.py`) — called only for High/Medium/Low clauses **when AI is enabled and `ANTHROPIC_API_KEY` is set**; asks Claude to rewrite the four-part breakdown in a more natural tone, *directly in the currently selected language* (`_lang`), and returns it as an overlay (`ai_breakdown`). System prompt uses `cache_control: ephemeral` for prompt caching across the batch. On any failure, the clause keeps its deterministic baseline plus a status key (`ai_note_key` / `ai_note_extra`) for the renderer to surface (or, per current UI choice, stay silent about — see *API key priority* below).

## Render-Time Localisation (critical — read before touching language-dependent code)

**`st.session_state["results"]` stores ONLY language-independent data**: the English deterministic `breakdown`, an optional `ai_breakdown` overlay, and status flags (`localized_by_ai`, `ai_note_key`, `ai_note_extra`). It deliberately does NOT store any final rendered/translated strings.

**ALL language-dependent text is resolved fresh, on every render pass**, inside `_build_results_html()` / `_build_exposure_summary_html()`, using the *current* `_lang`:
- If `localized_by_ai` is true, the AI's already-localised `ai_breakdown` is merged in directly (no machine translation needed).
- Otherwise, when `_lang != "English"`, each of the four breakdown parts is translated on the fly via `translate_text()` (`src/free_translate.py`, memoised by `(text, lang)`).
- Static UI chrome always goes through `t(key, lang)` (`src/i18n.py`).

**Why this matters:** Streamlit reruns the whole script on every interaction, but anything cached in `st.session_state` persists across reruns *unchanged* until explicitly overwritten. An earlier implementation baked translated strings into `results` at analysis time — which froze them at whatever language was active *during that one analysis run*, so later language switches silently did nothing to the dynamic explanations (only static chrome updated). **Do not reintroduce this bug**: never store a final translated/localised string in `st.session_state`; always resolve language-dependent text at render time using the live `_lang`.

The downloadable PDF report is the one deliberate exception — it stays English (deterministic baseline + any AI overlay, re-merged via `merge_breakdown()` right before `generate_report_pdf()` is called) since it's a reference document, and translating every clause's full text on every render just to build a string that's discarded unless downloaded would be wasted work.

## Multilingual Support (`src/i18n.py` + `src/free_translate.py`)

Two independent translation layers, both resolved at render time:

1. **Static UI chrome** — `t(key, lang)` does a plain dict lookup against `_STRINGS` in `src/i18n.py` (14 languages, English-first fallback for missing keys/languages). Deterministic, instant, no network calls — covers buttons, headers, risk badges, breakdown-part labels, notices, etc.
2. **Dynamic clause/exposure text** — the long, freely-composed English sentences from `clause_breakdown.py` and `financial_extractor.py` are NOT pre-translated by hand (word order/agreement differ too much across 14 languages for naive fragment substitution to work — see the module docstring in `i18n.py`). Instead, `translate_text(text, lang)` in `src/free_translate.py` calls a free machine-translation backend at runtime:
   - **Provider switch**: `_PROVIDER = os.getenv("FINCLARIX_TRANSLATE_PROVIDER", "google")`. `"google"` (default) uses the free, unofficial `translate.googleapis.com/translate_a/single` endpoint — no signup, no key, but unofficial and rate-limited. `"deepl"` uses DeepL's official Free API tier — genuinely free, higher quality, but requires `DEEPL_API_KEY`.
   - To switch providers: set `FINCLARIX_TRANSLATE_PROVIDER=deepl` and `DEEPL_API_KEY=...` in `.env` — **no code changes needed**.
   - `translate_text()` always returns `(text, ok)`. On any failure (network error, rate limit, missing DeepL key, …) it returns `(original_english, False)`, and the renderer shows a small `t("translation_unavailable_notice", lang)` notice instead of crashing or showing nothing.
   - Results are memoised via `@lru_cache(maxsize=1024)` keyed on `(text, lang)` — FinClariX's templated breakdown text repeats across clauses and reruns, so this avoids redundant network round-trips and keeps language switches fast.

## API Key Handling and No-Key Fallback Behaviour

- **Resolution order**: `load_dotenv(BASE_DIR / ".env")` runs once at startup; `os.environ["ANTHROPIC_API_KEY"]` is then read directly wherever the key is needed (`_get_client()` in `explanation_generator.py`, the `ai_enabled` checks in `app.py`). `st.session_state.api_key` exists as a session-level mirror but **the in-sidebar API-key text input has been intentionally removed from the UI** (per product decision — keeps secrets out of the browser/session-state and out of any UI-layer request logs); configure the key via `.env` / environment variables only.
- **`ai_enabled = _use_ai and bool(os.getenv("ANTHROPIC_API_KEY"))`** gates the optional Claude call. When it's `False` (AI toggled off, or no key present), every clause still gets its full deterministic breakdown from `build_breakdown()` — nothing is degraded except the *wording style* and *whether it's pre-localised by the AI*.
- **No-key / AI-disabled notice**: `app.py` sets `ai_note_key = "ai_disabled_notice"` in this case, but the renderer (`_build_results_html`) intentionally does **not** display it (`pass` — see the inline comment) per a later product decision to keep the clause cards visually clean. The breakdown content itself (rule-based, machine-translated when applicable) is shown exactly as normal.
- **AI failure paths** (`ai_note_key in ("ai_unavailable", "ai_error")`) still surface their notices — only the "AI is disabled" case was deliberately silenced.

## OCR Fallback (`src/pdf_reader.py`)

`OCR_AVAILABLE` is set at import time based on whether `pytesseract` (and, transitively, the Tesseract OCR engine) is importable/available — this is intentionally optional (commented out in `requirements.txt` by default, since it needs an OS-level binary). `extract_text_from_pdf()` tries the normal `pdfplumber` text-layer extraction first; if that yields nothing, `_ocr_fallback()` rasterises the PDF pages and runs Tesseract OCR on them. If `pytesseract` isn't available at all, `_ocr_fallback()` returns immediately and the app behaves exactly as it would without this module — no errors, just no OCR.

## PDF Report Generation (`src/report_generator.py`)

`generate_report_pdf(results, source_name, exposure_items) -> bytes` builds a polished PDF (via `fpdf2`, a free pure-Python library — no WeasyPrint/Cairo/Pango system dependencies) mirroring the structure of the original Markdown report: summary table, Financial Exposure Summary, then clauses grouped by risk level with their full four-part breakdowns. It is always built from the **English** baseline + any AI overlay (re-merged via `merge_breakdown()` at the call site in `app.py`, since `results[i]["breakdown"]` intentionally stores only the untouched deterministic baseline — see *Render-time localisation* above). `_pdf_safe()` defensively encodes text to Latin-1 (replacing unsupported characters with `?`) since fpdf2's built-in core fonts only cover Latin-1 — acceptable because the report is always English, but documented in case an AI overlay ever slips in non-Latin-1 wording. `pdf.output()` returns a `bytearray`; wrap in `bytes(...)` for `st.download_button(data=...)`.

**Risk keywords:** editing `data/risk_keywords.json` is the primary way to tune detection sensitivity — no code changes needed.
