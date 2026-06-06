# FinClariX 

> Finance that sticks, minus the tricks.

FinClariX is a web app that helps young expats and students understand financial contracts (rental agreements, bank account terms, etc.) by analysing them with AI and explaining each clause in plain language, with risk levels (High / Medium / Low) and multilingual support.

---

## Features

- Upload a financial contract (PDF)
- Select your preferred language
- Get each clause explained in simple language
- Risk classification: 🔴 High / 🟡 Medium / 🟢 Low
- Instant results, no appointments needed

---

## Setup & Run

FinClariX is launch-location independent — clone it anywhere and run it from
the project root with:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Then, optionally, add your Anthropic API key so clauses get AI-polished
explanations on top of the built-in rule-based breakdown:

```bash
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

The app works fully without an API key — risk detection, the four-part clause
breakdown, and the financial exposure summary are all rule-based and run
locally; the API key only adds AI-polished wording on top.

---

## Tech Stack

- **UI:** [Streamlit](https://streamlit.io)
- **PDF text extraction:** [pdfplumber](https://github.com/jsvine/pdfplumber), with an optional OCR fallback (`pytesseract`) for scanned/image-only PDFs
- **Risk detection:** deterministic keyword matching against `data/risk_keywords.json`
- **Financial exposure extraction:** rule-based regex parsing of monetary amounts and time periods (`src/financial_extractor.py`)
- **AI explanations:** [Anthropic Claude API](https://docs.claude.com) via the `anthropic` SDK — optional, polishes wording on top of the deterministic breakdown
- **Config:** `python-dotenv` loads `ANTHROPIC_API_KEY` from a local `.env` file
................................................


## Authors

- Myriam B. Guijarro Santiago
- Zhentong Zhou

Rotterdam School of Management — MSc Business Analytics & Management
