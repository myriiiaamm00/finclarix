# FinClariX

> "Finance that sticks, minus the tricks."

FinClariX is a Streamlit web app that helps young expats and students
understand financial contracts — rental agreements, bank account terms, and
similar documents — by breaking them down clause by clause, flagging the
risky parts in plain language, and quantifying what those clauses could
actually cost. It supports 14 interface languages and works completely free
of charge, with optional AI-polished explanations layered on top when an
Anthropic API key is configured.

This repository is the MVP submission for **FinTech Assignment 2** (Rotterdam
School of Management, MSc Business Analytics & Management), building on the
business model proposed in Assignment 1.

---

## Project Overview

Signing a financial contract in a foreign country, in a foreign language, is
one of the first hurdles a young expat or exchange student faces — usually
within days of arriving, and usually under time pressure (landlords expect a
signed lease within 24–48 hours; banks expect onboarding documents signed on
the spot). FinClariX turns that contract into something closer to a
conversation with "the financially literate friend who reads your contract
before you sign it": upload a PDF (or paste the text), and the app splits it
into clauses, scans each one for known risk patterns, classifies it as
High / Medium / Low / Informational risk, and explains — in the user's own
language — what it actually means, why it matters, what it could cost, and
what to do about it before signing.

## Problem Statement

Today, someone facing a confusing financial contract abroad has two
realistic options, and both fall short:

- **Professional legal advice** (solicitors, notaries, financial advisors)
  costs €100–400/hour, requires appointments and advance booking, takes days
  to deliver, and is written in language that assumes financial literacy —
  completely incompatible with a student on a €700/month budget who needs an
  answer *today*.
- **Generic translation tools** (Google Translate, DeepL, general-purpose AI
  document analysers) are fast and cheap, but they translate language without
  interpreting *meaning*. They treat a penalty clause exactly like the rest of
  the document, so terms like "effective annual rate" or "non-refundable
  deposit" come through grammatically correct and substantively meaningless to
  someone without a finance background — and nothing tells the reader which
  three sentences in a five-page contract are the ones that can actually hurt
  them financially.

FinClariX is built to close that specific gap: not a better translator, but a
**risk-aware financial interpreter** that surfaces what matters and explains
it the way a friend would.

## Target Users

FinClariX targets young people aged 18–30 who are relocating abroad — primarily
international students (e.g. on Erasmus+ exchanges) and junior professionals in
their first role overseas. This group is characterised by limited financial
literacy, high exposure to complex contracts in a short window (rental lease,
bank account, sometimes an employment contract — all within the first weeks),
low willingness or ability to pay for professional advice, and very high
smartphone/web adoption. The MVP initially focuses on the European market,
where Erasmus+ mobility is large and growing and a single regulatory
framework (GDPR) simplifies building one compliant product for the whole
region.

## MVP Features

- **Two ways to bring in a contract** — upload a PDF or paste raw text
  directly, whichever is faster for the situation at hand.
- **Automatic clause splitting and risk scanning** — the contract is split
  into individual clauses, each scanned against a configurable keyword list
  (`data/risk_keywords.json`) and scored as **High / Medium / Low /
  Informational** risk.
- **Four-part plain-language breakdown per risky clause** — *Plain-language
  explanation*, *Why it matters*, *Potential financial impact*, and
  *Suggested action before signing*, generated deterministically so the app
  is fully useful even with zero configuration (`src/clause_breakdown.py`).
- **Financial Exposure Summary** — goes a step further than flagging risk: it
  extracts the actual amounts and time periods stated in the contract and
  computes concrete, quantified exposure (e.g. *"this early-termination clause
  could cost you up to €4,050 — three months of your €1,350 rent"*),
  deterministically and without AI (`src/financial_extractor.py`). This is the
  feature that most directly differentiates FinClariX from a generic
  translator: it doesn't just say *"this looks risky"*, it says *how much*.
- **Multilingual interface and explanations** — 14 supported languages,
  switchable at any time from the sidebar, with every part of the UI and every
  clause explanation updating immediately (see *Multilingual support* below).
- **Optional AI-polished explanations** — when an Anthropic API key is
  configured, Claude rewrites each clause's breakdown in a more natural,
  conversational tone — directly in the selected language — on top of the
  deterministic baseline (`src/explanation_generator.py`).
- **Zero-cost translation fallback** — even without any API key, non-English
  users still get every clause explanation translated via a free machine
  translation backend, with graceful fallback to English if translation is
  ever unavailable (`src/free_translate.py`).
- **Optional OCR for scanned contracts** — image-only PDFs (no embedded text
  layer) are run through Tesseract OCR automatically, so scanned leases and
  photographed bank documents can be analysed too (`src/pdf_reader.py`).
- **Downloadable PDF report** — a polished, ready-to-print PDF summarising the
  whole analysis (risk summary, financial exposure, full clause-by-clause
  breakdown) that the user can save or share (`src/report_generator.py`).
- **Runs fully without any paid service** — every core feature (clause
  splitting, risk detection, financial exposure, the four-part breakdown, the
  multilingual interface, and machine-translated explanations) works with zero
  API keys and zero recurring cost. AI and translation only ever *enhance* a
  baseline that already works — they never gate it.

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| UI | [Streamlit](https://streamlit.io) | Single-page app, all state in `st.session_state` |
| PDF text extraction | [pdfplumber](https://github.com/jsvine/pdfplumber) | `src/pdf_reader.py` |
| OCR fallback (optional) | [pytesseract](https://github.com/madmaze/pytesseract) + Tesseract OCR engine | Only used when a PDF has no embedded text layer |
| Risk detection | Deterministic keyword matching | `data/risk_keywords.json`, `src/risk_detector.py`, `src/risk_scoring.py` |
| Deterministic clause breakdown | Rule-based templates, categorised by clause topic | `src/clause_breakdown.py` |
| Financial exposure extraction | Regex + arithmetic over amounts/time periods | `src/financial_extractor.py` |
| AI explanations (optional) | [Anthropic Claude API](https://docs.claude.com) via the `anthropic` SDK | `src/explanation_generator.py`, prompt-cached |
| Static UI translation | Custom i18n lookup table, 14 languages | `src/i18n.py` |
| Dynamic explanation translation | Free machine-translation backends (Google Translate / DeepL Free), stdlib `urllib` only | `src/free_translate.py` |
| PDF report generation | [fpdf2](https://github.com/py-pdf/fpdf2) — pure-Python, MIT/LGPL, no system dependencies | `src/report_generator.py` |
| Configuration | `python-dotenv` loads `ANTHROPIC_API_KEY` (and optional translation settings) from `.env` | `.env.example` |

## Architecture and Analysis Pipeline

```
app.py                        ← Streamlit entry point; all UI state in st.session_state
src/
  pdf_reader.py               ← extract_text_from_pdf() [+ OCR fallback] and split_into_clauses()
  risk_detector.py            ← load_keywords() + detect_risks() per clause
  risk_scoring.py             ← score_clause() → "High" | "Medium" | "Low" | "Informational"
  clause_breakdown.py         ← build_breakdown() → deterministic 4-part explanation, no AI required
  financial_extractor.py      ← find_rent_amount(), build_exposure_summary() → quantified € exposure
  explanation_generator.py    ← explain_clause() → optional AI-polished, localised rewrite via Claude
  free_translate.py           ← translate_text() → free, runtime machine translation fallback
  i18n.py                     ← t(key, lang) → static UI-chrome translations across 14 languages
  report_generator.py         ← generate_report_pdf() → polished downloadable PDF report
data/
  risk_keywords.json          ← {"high": [...], "medium": [...], "low": [...]}
sample_contracts/             ← .txt files for quick testing via the "Paste Text" tab
```

**The pipeline, end to end:**

1. **Extraction** — `extract_text_from_pdf()` pulls text from the uploaded
   PDF (falling back to OCR if there's no embedded text layer), then
   `split_into_clauses()` splits it into individual clauses using regex rules
   for numbered sections, "Article" headings, or paragraph breaks.
2. **Risk detection** — `detect_risks()` matches each clause's text against
   the High/Medium/Low keyword lists in `data/risk_keywords.json`; `score_clause()`
   converts the matches into a single risk level (highest match wins; no match
   → *Informational*).
3. **Deterministic breakdown** — `build_breakdown()` produces the four-part
   explanation for every risky clause using topic-aware templates (a deposit
   clause and an arbitration clause are both "high-risk" but get very
   different wording) — this always runs, with or without an API key.
4. **Financial exposure** — `build_exposure_summary()` independently scans the
   whole contract for stated amounts (rent, fees, deposits, notice periods,
   …) and computes concrete projected costs — also fully deterministic.
5. **Optional AI layer** — if AI is enabled and a key is configured,
   `explain_clause()` asks Claude to rewrite the four-part breakdown for that
   specific clause in a more natural, conversational tone, directly in the
   user's selected language (the system prompt uses `cache_control: ephemeral`
   for prompt caching across the batch, keeping repeated calls cheap).
6. **Render-time localisation** — every piece of on-screen text is resolved
   *fresh on every render* using the currently selected language: static UI
   chrome via `t()`, and dynamic clause text via either the AI's localised
   output (if available) or `translate_text()` as a free fallback. This is
   what makes switching languages update everything immediately, without
   re-running the analysis (see *Multilingual support* below for why this
   matters).
7. **Reporting** — on request, `generate_report_pdf()` assembles the full,
   English-language analysis (deterministic baseline + any AI-polished
   overlay) into a downloadable PDF.

**Tuning risk sensitivity:** editing `data/risk_keywords.json` is the primary
way to adjust what gets flagged — no code changes required.

## How to Run Locally

FinClariX is launch-location independent — clone it anywhere and run it from
the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`. No further setup is
required — every core feature works out of the box, with zero API keys.

To enable AI-polished, localised explanations on top of the deterministic
baseline, configure an Anthropic API key:

```bash
cp .env.example .env
# then edit .env and set: ANTHROPIC_API_KEY=sk-ant-...
```

(Optional) For OCR support on scanned/image-only PDFs, also install the
Tesseract OCR engine on your system (`brew install tesseract` on macOS,
`sudo apt-get install tesseract-ocr` on Ubuntu) and uncomment `pytesseract` in
`requirements.txt`.

## How to Use the App

1. **Choose your language and AI mode** in the sidebar — pick one of 14
   interface languages, and toggle AI-polished explanations on or off.
2. **Bring in a contract** — either upload a PDF in the *Upload* tab, or paste
   raw contract text in the *Paste Text* tab (a few sample contracts are
   included in `sample_contracts/` if you want to try it immediately).
3. **Click "Analyse Contract"** — the app extracts the text, splits it into
   clauses, scores each one's risk level, and builds the explanations.
4. **Read the results** — clauses are grouped by risk level (🔴 High / 🟡
   Medium / 🟢 Low / ℹ️ Informational), each with its four-part breakdown,
   alongside a Financial Exposure Summary that quantifies the contract's
   biggest potential costs.
5. **Switch languages anytime** — changing the language selector instantly
   re-renders every explanation and UI label in the new language, with no
   need to re-analyse the contract.
6. **Download the PDF report** — get a polished, shareable summary of the
   whole analysis to keep or send to someone else for a second opinion.

## Multilingual Support

FinClariX supports **14 interface languages**. Multilingual support works at
two distinct levels, both of which update *immediately* when the language
selector changes — no re-analysis required:

- **Static UI chrome** (buttons, section headers, risk badges, breakdown
  labels, notices, …) is translated via a small lookup table in `src/i18n.py`
  — deterministic, instant, no network calls.
- **Dynamic clause explanations** (the long, freely-composed sentences
  produced by the deterministic breakdown or the AI layer) are resolved
  *at render time*: if the AI already produced localised wording, that's used
  directly; otherwise the English baseline is machine-translated on the fly
  via `src/free_translate.py` (see next section).

Resolving all of this at render time — rather than baking translated strings
into session state when the contract is first analysed — is what guarantees
that flipping the language selector updates *everything* on screen instantly,
including any "translation unavailable" notices, exactly as the business plan
promises ("everyone can choose their preferred language").

## AI Explanations and Zero-Cost Translation Fallback

FinClariX is designed so that **AI is always an enhancement, never a
requirement** — directly mirroring the freemium-to-premium structure of the
underlying business model:

- **Without any API key**, every clause still gets a complete four-part
  breakdown from the deterministic, topic-aware template engine in
  `src/clause_breakdown.py`, and — for non-English users — that breakdown is
  translated on the fly via a **free machine translation backend**
  (`src/free_translate.py`). By default this uses the free, unofficial Google
  Translate web endpoint (no signup, no key); it can be switched to DeepL's
  official Free API tier instead by setting `FINCLARIX_TRANSLATE_PROVIDER=deepl`
  and `DEEPL_API_KEY=...` in `.env` — no code changes required. Translation
  results are cached (by text + language) to stay fast and avoid hammering the
  free endpoint, and any failure degrades gracefully to the English original
  with a small "Translation unavailable — showing English" notice.
- **With an Anthropic API key configured**, `explain_clause()` additionally
  asks Claude to rewrite each risky clause's breakdown in a more natural,
  conversational, "financially-savvy-friend" tone — directly in the selected
  language — layered on top of (and never replacing) the deterministic
  baseline. If the AI call fails for any reason, the app falls back to the
  rule-based breakdown plus machine translation without interrupting the
  user's session.

This three-layer design (deterministic baseline → optional AI polish →
optional machine translation) is what lets FinClariX promise "mother-tongue
explanations for everyone" without requiring a single paid subscription to
function.

## Optional OCR Support

Some contracts only exist as scanned images — a photographed lease, a PDF with
no embedded text layer. `src/pdf_reader.py` detects this case automatically
and falls back to Tesseract OCR (via `pytesseract`) to extract text from the
page images, so the rest of the pipeline can run exactly as it would for a
digital PDF. This is entirely optional: if `pytesseract` isn't installed (it's
commented out in `requirements.txt` by default, since it also needs the
Tesseract OCR engine installed at the OS level), the app simply skips OCR and
behaves exactly as before — uploads without an embedded text layer will report
that no text could be extracted, rather than erroring out.

## Report Generation

At the end of an analysis, users can download a polished **PDF report**
(`generate_report_pdf()` in `src/report_generator.py`, built with
[fpdf2](https://github.com/py-pdf/fpdf2) — a free, pure-Python PDF library
with no system dependencies). The report includes a risk-level summary table,
the Financial Exposure Summary, and the full clause-by-clause breakdown
(deterministic baseline merged with any AI-polished overlay), all in English —
intended as a stable, shareable reference document regardless of which display
language was active in the session. This single-document export is also a
working preview of the "Integrated Reporting Tools (PDF/CSV)" feature
envisioned for the institutional (B2B/university) tier of the business model.

## Deployment Notes

The MVP is a standard Streamlit app and can be run:

- **Locally**, as described above — the simplest path for grading/demo
  purposes, and the one this repository is configured for.
- **On Streamlit Community Cloud** or any other Streamlit-compatible hosting
  platform, by pointing it at this repository's `app.py` and configuring
  `ANTHROPIC_API_KEY` (and, optionally, `FINCLARIX_TRANSLATE_PROVIDER` /
  `DEEPL_API_KEY`) as platform-level secrets rather than a local `.env` file.
- **Behind a reverse proxy / containerised**, for a more production-like
  deployment — `streamlit run app.py --server.port $PORT --server.address
  0.0.0.0` is the relevant entry point; no code changes are required.

For the path described in the business plan (a B2C mobile app with B2B
co-branded institutional deployments), this Streamlit MVP is best understood
as a fast way to validate the core analysis pipeline and UX before investing
in native mobile development — see *Limitations* and *Future development*
below.

## Security and Privacy Considerations

- **No API keys are entered or stored through the UI.** The Anthropic API key
  (and any optional translation provider key) is read exclusively from
  environment variables / a local `.env` file via `python-dotenv`. This keeps
  secrets out of the browser, out of `st.session_state`, and out of any
  request logs the UI layer might produce.
- **Contracts are processed in memory for the current session only.** The app
  does not persist uploaded documents, extracted text, or analysis results to
  disk or to any external database — everything lives in `st.session_state`
  and disappears when the session ends or the page is refreshed.
- **Outbound calls are limited and explicit.** The only external services the
  app talks to are the Anthropic API (only if a key is configured and AI mode
  is on) and a free machine-translation endpoint (only for non-English
  display languages, and only for the already-deterministic English text — no
  user-identifying information is sent). Clause text is sent to these services
  exactly when, and only when, the user has opted into the corresponding
  feature.
- **Operator-side risks to plan for at production scale** include: securing
  whatever storage layer is added for "historical contract tracking" (a
  promised premium feature, not yet implemented — see *Limitations*), GDPR-
  compliant handling of what is inherently sensitive personal/financial
  document content, rate-limiting and abuse protection on AI and translation
  calls, and key-rotation practices for the Anthropic and translation provider
  credentials.
- **User-side risks to be transparent about** include: the free, unofficial
  translation endpoint is not a contractual data-processing relationship (it
  should not be relied on for sensitive documents in a production deployment —
  the DeepL Free tier, which has a documented API and terms of service, is the
  safer default to switch to before going live), and AI-polished explanations
  are model output and should always be treated as a starting point for the
  user's own judgement, not as a substitute for it (see *Disclaimer*).

## Limitations

This MVP intentionally prioritises validating the **core analysis pipeline and
multilingual UX** over building out the full product described in the
business plan. Known gaps, to be addressed honestly rather than glossed over:

- **No persistence or user accounts.** There is no database, no login, and no
  "historical contract tracking" — every analysis is ephemeral. This is a
  prerequisite for both the paid B2C tier and any B2B batch-processing
  features.
- **Risk detection is keyword- and template-based, not a fine-tuned model.**
  The business plan envisions an LLM trained specifically on financial
  contract datasets; this MVP uses transparent, auditable keyword matching and
  topic-aware templates as its deterministic baseline (with optional Claude
  polish on top). This was a deliberate choice for an MVP — it's fast,
  explainable, free to run, and easy to tune (`data/risk_keywords.json`) — but
  it will miss risk patterns that don't match its keyword lists or fall
  outside its template categories.
- **The free translation backend is an unofficial, rate-limited endpoint.**
  It's adequate for demonstrating zero-cost multilingual support, but it could
  fail under heavy concurrent use (the app degrades gracefully when it does,
  showing English with a notice — but a production deployment would want to
  default to a backend with an actual SLA, e.g. DeepL's official Free/Pro
  tiers, which `free_translate.py` already supports via a one-line config
  change).
- **Web app, not the mobile-first native app the business plan describes.**
  Streamlit was chosen to validate the analysis pipeline and UX quickly and
  cheaply; a native (or cross-platform) mobile app remains a separate,
  larger investment for a later stage.
- **Single-document workflow.** There's no batch processing, side-by-side
  contract comparison, or analytics dashboard — all of which are part of the
  envisioned B2B/institutional offering.

## Future Development

Roughly in the order they would unlock the next layer of the business model:

1. **Accounts and persistent contract history** — the prerequisite for the
   paid B2C "Standard" tier (`€5/month` — unlimited uploads, history tracking)
   and for any institutional reporting.
2. **A production-grade translation/localisation backend** — moving from the
   free fallback endpoint to DeepL's official tier (already wired in as a
   one-line config switch) or a properly licensed, fine-tuned multilingual
   model.
3. **A specialised contract-analysis model** — replacing/augmenting the
   keyword-and-template baseline with a model fine-tuned (or RAG-grounded) on
   financial contract corpora, to push detection accuracy toward the ≥90%
   target the business plan sets as a key success factor.
4. **Batch processing, dashboards, and co-branding** — the concrete features
   that turn the current single-user MVP into the B2B/university offering
   described in the business plan (custom branding, bulk contract processing,
   analytics dashboards, SLA support).
5. **A native mobile app** — the long-term target platform for the primary
   B2C audience, once the underlying pipeline and UX have been validated (as
   this MVP is intended to do).

## AI Agents and Orchestration

This MVP was built with the assistance of Claude (via the Claude Agent SDK /
Cowork, building on Claude Code) as the primary coding agent, working
alongside the two-person human team in an iterative, review-and-refine loop.
The full account of which agents were used, why, how they were orchestrated,
and how the human team reviewed and directed the work lives in
[`AGENTS.md`](./AGENTS.md) — kept as the single source of truth for this topic
so it doesn't drift out of sync with this README.

## Disclaimer

**FinClariX is an educational MVP built for FinTech Assignment 2 and does not
provide legal or financial advice.** Its explanations — whether deterministic,
AI-polished, or machine-translated — are generated automatically and may be
incomplete, imprecise, or simply wrong. Nothing in this app should be relied
upon as a substitute for consulting a qualified solicitor, notary, or
financial advisor before signing a binding contract. Always read the original
document carefully and seek professional advice for anything you don't fully
understand.

## Authors

- Myriam B. Guijarro Santiago
- Zhentong Zhou

Rotterdam School of Management — MSc Business Analytics & Management
