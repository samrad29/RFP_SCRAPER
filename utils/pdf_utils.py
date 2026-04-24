import fitz  # PyMuPDF
import requests
from scraping_utils import REQUEST_TIMEOUT_S
from pdf2image import convert_from_bytes
import pytesseract

def extract_pdf_text(pdf_bytes: bytes) -> tuple[str, str]:
    """
    Extract the text from a PDF file using pymupdf if possible, otherwise use OCR.
    Returns (text, method_used)
    """
    text = extract_text_pymupdf(pdf_bytes)

    if is_text_valid(text):
        return text, "pymupdf"
    else:
        text = ocr_extract_pdf_text(pdf_bytes)
        return text, "ocr"


def download_pdf(url: str, session: requests.Session) -> bytes:
    """
    Just download the pdf from the link
    """
    resp = session.get(url, timeout=REQUEST_TIMEOUT_S)
    resp.raise_for_status()
    return resp.content


def extract_text_pymupdf(pdf_bytes: bytes) -> str:
    """
    Extract the text from a PDF file using PyMuPDF. 
    This is the prefered method for extracting text from PDFs.
    It is more accurate than the other methods and is faster.
    """
    text = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text.append(page.get_text())

    return "\n".join(text)


def is_text_valid(text: str) -> bool:
    """
    Check to see if the text extraction worked 
        (presumably if there are more than 200 characters it probably worked)
    """
    if not text:
        return False
    if len(text.strip()) < 200:  # too short
        return False
    return True

def ocr_extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extract the text from a PDF file using OCR.
    This is a fallback method for extracting text from PDFs.
    It is less accurate than the other methods and is slower.
    """
    images = convert_from_bytes(pdf_bytes)
    text = []
    for image in images:
        page_text = pytesseract.image_to_string(image)
        text.append(page_text)

    return "\n".join(text)