import re
import pdfplumber


def extract_text_from_pdf(uploaded_file) -> str:
    with pdfplumber.open(uploaded_file) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n\n".join(pages)


def split_into_clauses(text: str) -> list[str]:
    # Try section-header splitting first (numbered, Article N, Section N, roman numerals)
    section_pattern = re.compile(
        r'(?=(?:\d+\.\d*|Article\s+\d+|Section\s+\d+|ARTICLE\s+\d+|SECTION\s+\d+|[IVX]+\.)\s)',
        re.IGNORECASE,
    )
    parts = section_pattern.split(text)

    # Fall back to paragraph splitting if section split yields too little
    if len(parts) < 3:
        parts = re.split(r'\n{2,}', text)

    clauses = [c.strip() for c in parts if len(c.strip()) >= 50]
    return clauses
