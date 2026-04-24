from __future__ import annotations

import hashlib
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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
            resp = sess.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=REQUEST_TIMEOUT_S,
                allow_redirects=True,
            )
            resp.raise_for_status()
            return resp.text
        except (requests.RequestException, OSError) as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_S * (attempt + 1))
            else:
                raise last_exc from None
    raise RuntimeError("unreachable")

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