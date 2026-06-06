import re

import pdfplumber

# OCR is an OPTIONAL fallback for scanned/image-only PDFs that have no
# embedded text layer (pdfplumber's extract_text() returns nothing for these).
# It depends on `pytesseract` (a thin wrapper around the Tesseract OCR engine)
# plus the Tesseract binary itself being installed on the host machine —
# neither of which ships with the core requirements.txt.
#
#   pip install pytesseract
#   macOS:   brew install tesseract
#   Ubuntu:  sudo apt-get install tesseract-ocr
#
# If pytesseract isn't available, OCR is silently skipped and the app behaves
# exactly as before — normal (text-based) PDFs are completely unaffected.
try:
    import pytesseract

    OCR_AVAILABLE = True
except ImportError:
    pytesseract = None
    OCR_AVAILABLE = False


def extract_text_from_pdf(uploaded_file) -> str:
    """Extract text from a PDF. Tries the normal embedded-text layer first
    (fast, accurate); if that comes back empty and OCR is available, falls
    back to rendering each page as an image and running OCR on it."""
    with pdfplumber.open(uploaded_file) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    text = "\n\n".join(pages)

    if not text.strip():
        ocr_text = _ocr_fallback(uploaded_file)
        if ocr_text.strip():
            return ocr_text

    return text


def _ocr_fallback(uploaded_file) -> str:
    """Best-effort OCR for pages with no embedded text. Returns "" whenever
    OCR isn't available or fails for any reason — callers treat that the same
    as 'no text found', so this can never break the normal PDF workflow."""
    if not OCR_AVAILABLE:
        return ""

    try:
        seek = getattr(uploaded_file, "seek", None)
        if callable(seek):
            seek(0)
    except Exception:
        pass

    try:
        texts = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                image = page.to_image(resolution=200).original
                texts.append(pytesseract.image_to_string(image))
        return "\n\n".join(texts)
    except Exception:
        # Missing Tesseract binary, unsupported page, render failure, etc. —
        # OCR is optional, so we degrade quietly rather than raising.
        return ""


def split_into_clauses(text: str) -> list[str]:
    # Try section-header splitting first (numbered, Article N, Section N, roman numerals).
    #
    # IMPORTANT: the pattern is anchored to the START OF A LINE (^ + re.MULTILINE)
    # rather than matched anywhere in the text. Without that anchor, a lookahead
    # like `(?=\d+\.\s)` happily matches in the *middle* of "10. PERSONAL GUARANTEE"
    # (splitting it into "...1" + "0. PERSONAL GUARANTEE...") or inside an
    # abbreviation like "Green Oak Properties B.V." (splitting into "...B." +
    # 'V. ("Landlord")...'). Real section headers always start a line, so anchoring
    # to line-start eliminates these false positives while still matching genuine
    # numbered sections, Articles, Sections, and roman-numeral headings.
    # Kept as a zero-width lookahead (?=...) so re.split() doesn't consume the
    # matched header text — each resulting clause still starts with its own
    # "10. PERSONAL GUARANTEE" / "Article 5" / "III." heading, exactly as the
    # original (unanchored) pattern intended.
    section_pattern = re.compile(
        r'(?=^[ \t]*(?:\d+\.\d*|Article\s+\d+|Section\s+\d+|ARTICLE\s+\d+|SECTION\s+\d+|[IVXLCDM]+\.)\s)',
        re.IGNORECASE | re.MULTILINE,
    )
    parts = section_pattern.split(text)

    # Fall back to paragraph splitting if section split yields too little
    if len(parts) < 3:
        parts = re.split(r'\n{2,}', text)

    clauses = [c.strip() for c in parts if len(c.strip()) >= 50]
    return clauses
