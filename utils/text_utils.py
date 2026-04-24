import re
from typing import Optional

# Precompiled regexes for performance (important at scale)
PAGE_NUMBERS = re.compile(r"\bPage\s+\d+(\s+of\s+\d+)?\b", re.IGNORECASE)
MULTI_SPACES = re.compile(r"[ \t]+")
EXCESS_NEWLINES = re.compile(r"\n{3,}")
HYPHEN_LINEBREAK = re.compile(r"-\n")
HEADER_FOOTER_GARBAGE = re.compile(r"^\s*\d+\s*$", re.MULTILINE)

def clean_text(text: str, *, preserve_lines: bool = True) -> str:
    """
    Production-grade text normalization for unstructured documents (PDF/HTML/OCR).
    
    Designed for downstream LLM extraction.
    """
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = HYPHEN_LINEBREAK.sub("", text)
    text = PAGE_NUMBERS.sub("", text)
    text = HEADER_FOOTER_GARBAGE.sub("", text)
    text = MULTI_SPACES.sub(" ", text)
    if preserve_lines:
        text = EXCESS_NEWLINES.sub("\n\n", text)
    else:
        text = EXCESS_NEWLINES.sub("\n", text)
        text = text.replace("\n", " ")

    return text.strip()