import requests
from utils.scraping_utils import extract_rfp_links
from utils.scraping_utils import fetch_html

def test_rfp_link_extraction(url: str, session: requests.Session) -> list[dict]:
    """
    Test the RFP link extraction
    """
    html_response = fetch_html(url, session)
    if not html_response.get("success"):
        return []
    return extract_rfp_links(html_response["html"], url, session)


if __name__ == "__main__":
    session = requests.Session()
    url = "https://stcroixojibwe-nsn.gov/government/grants/"
    rfp_links = test_rfp_link_extraction(url, session)
    print(rfp_links)