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


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _largest_text_div(soup: BeautifulSoup):
    best = None
    best_len = 0
    for div in soup.find_all("div"):
        t = div.get_text(" ", strip=True)
        n = len(t)
        if n > best_len:
            best_len = n
            best = div
    return best


def extract_main_content(soup: BeautifulSoup) -> str:
    root = (
        soup.select_one("#DeltaPlaceHolderMain")
        or soup.select_one("#MainContent")
        or soup.select_one("#content")
        or soup.select_one("main")
        or soup.select_one('[role="main"]')
    )
    if root is None:
        root = _largest_text_div(soup) or soup.body
    if root is None:
        return ""
    text = extract_clean_text(root)
    if not text.strip():
        text = root.get_text("\n", strip=True)
    return text.strip()


RFP_KEYWORDS = ["rfp", "proposal", "bid", "rfq", "itb"]

def extract_rfp_links(html, base_url):
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
                "type": "pdf" if url.endswith(".pdf") else "html"
            })

    return candidates
