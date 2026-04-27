import re
from typing import Optional

# Things to remove from the text to make it easier to parse
PAGE_NUMBERS = re.compile(r"\bPage\s+\d+(\s+of\s+\d+)?\b", re.IGNORECASE)
MULTI_SPACES = re.compile(r"[ \t]+")
EXCESS_NEWLINES = re.compile(r"\n{3,}")
HYPHEN_LINEBREAK = re.compile(r"-\n")
HEADER_FOOTER_GARBAGE = re.compile(r"^\s*\d+\s*$", re.MULTILINE)

def clean_text(text: str, *, preserve_lines: bool = True) -> str:
    """
    Clean the text by removing extra whitespace and newlines
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

def better_extraction_text(text: str) -> str:
    """
    Make the text easier to extract data from, bring in the start of the text 
    and then find relevant parts of the  remaining text
    """
    try:
        # Find the start of the text
        return_text = "--- TEXT START ---\n"
        return_text += "\n--- Text Head Start ---\n"
        text_head = text[:5000]
        return_text += (text_head)
        return_text += "\n--- Text Head End ---\n"
        
        # Find the 5 most relevante chunks of the text (using keywords)
        remaining_text = text[5000:]
        keywords = ["deadline", "project size", "categories", "description", "scope of work", "scope", "qualifications"]
        chunks = chunk_text(remaining_text, keywords)
        relevant_chunks = chunks[:5]

        i = 0
        for chunk in relevant_chunks:
            return_text += f"\n--- Text Chunk {i} Start ---\n"
            start_idx = max(0, chunk[0])
            end_idx = min(len(remaining_text), chunk[1])
            return_text += remaining_text[start_idx:end_idx]
            return_text += f"\n--- Text Chunk {i} End ---\n"
            i += 1

        return_text += ("\n--- TEXT END ---\n")
        return return_text
    except Exception as e:
        print(f"Error in better_extraction_text: {e}")
        return "--- TEXT START ---\n" + text[:5000] + "\n--- TEXT END ---\n"

def chunk_text(text: str, keywords: list[str]) -> list[tuple[int, int]]:
    """
    Chunk the text into 5 most relevant chunks using keywords
    """
    chunk_size = 500
    overlap = 100
    chunks = []
    lowered_keywords = [k.lower() for k in keywords]
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        chunk_lower = chunk.lower()
        score = 0
        for keyword in lowered_keywords:
            score += chunk_lower.count(keyword)
        chunks.append((i, i + chunk_size, score))

    chunks.sort(key=lambda x: x[2], reverse=True)
    return chunks