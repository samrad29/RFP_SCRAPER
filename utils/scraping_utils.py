from __future__ import annotations

import hashlib
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils.pdf_utils import download_pdf, extract_pdf_text
from utils.text_utils import clean_text

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT_S = 30
MAX_RETRIES = 2
RETRY_BACKOFF_S = 1.5

RFP_KEYWORDS = ["rfp", "proposal", "bid", "rfq", "itb", "rfqa"]

def fetch_html(url: str, session: requests.Session | None = None) -> str:
    sess = session or requests.Session()
    last_exc: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            # First attempt: normal SSL
            resp = sess.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=REQUEST_TIMEOUT_S,
                allow_redirects=True,
                verify=True,
            )
            resp.raise_for_status()
            return {"success": True, "html": resp.text}

        # could try to scrape without verifying the SSL cert, but it is risky and should investigate more
        # except requests.exceptions.SSLError as ssl_err: 
        #     # If SSL error, try to scrape without verifying the SSL cert (maybe a little risky, should investigate more)
        #     print(f"[SSL ERROR] {url} — retrying without verification")
        #     last_exc = ssl_err
        #     try:
        #         resp = sess.get(
        #             url,
        #             headers=DEFAULT_HEADERS,
        #             timeout=REQUEST_TIMEOUT_S,
        #             allow_redirects=True,
        #             verify=False,
        #         )
        #         resp.raise_for_status()
        #         return resp.text

        #     except Exception as fallback_err:
        #         last_exc = fallback_err

        except (requests.RequestException, OSError) as e:
            last_exc = e

        if attempt < MAX_RETRIES: # If we have not retried the max number of times, sleep and retry
            time.sleep(RETRY_BACKOFF_S * (attempt + 1))
        else:
            return {"message": str(last_exc), "success": False} # If we have retried the max number of times, raise the last exception
    return {"message": f"Failed to fetch {url}", "success": False}

def extract_rfp_links(html, base_url, session: requests.Session):
    soup = BeautifulSoup(html, "lxml")

    candidates = []

    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]

        url = urljoin(base_url, href)

        combined = f"{text} {url}".lower()

        if any(k in combined for k in RFP_KEYWORDS):
            candidates.append({
                "title": text,
                "url": url,
                "type": classify_content_type(url, session)
            })

    return candidates

def classify_content_type(url: str, session: requests.Session) -> str:
    """
    Classify the content type of the URL
    Try to use the HEAD request to get the content type, 
    if that fails, use the GET request to get the content type from the first few bytes.
    """
    path = urlparse(url).path.lower()

    if path.endswith(".pdf"):
        return "pdf"

    if "viewdocument" in url.lower():
        return "pdf"

    try:
        resp = session.head(url, allow_redirects=True, timeout=REQUEST_TIMEOUT_S)
        content_type = resp.headers.get("Content-Type", "").lower()

        if "pdf"in content_type:
            return "pdf"
        if "html" in content_type:
            return "html"
    except Exception:
        pass
    try:
        resp = session.get(url, stream=True, timeout=REQUEST_TIMEOUT_S)
        if resp.status_code == 200:
            content_type = resp.headers.get("Content-Type", "").lower()
            if "pdf" in content_type:
                return "pdf"
            if "html" in content_type:
                return "html"
        else: 
            return "unknown"
    except Exception:
        return "unknown"

def get_link_text(rfp_link: dict, session: requests.Session) -> str:
    if rfp_link["type"] == "html":
        html = fetch_html(rfp_link["url"], session)
        if html["success"]:
            return clean_text(html["html"])
        else:
            return None
    elif rfp_link["type"] == "pdf":
        pdf_bytes = download_pdf(rfp_link["url"], session)
        if pdf_bytes:
            text, method_used = extract_pdf_text(pdf_bytes)
            return text
        else:
            return None
    else:
        return None