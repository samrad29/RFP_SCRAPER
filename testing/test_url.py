
from utils.scraping_utils import get_link_text
import requests
from utils.scraping_utils import fetch_html
from utils.ai_utils.prompts import ai_classify_rfp
from utils.ai_utils.llm_utils import TokenTracker
from groq import Groq
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")
from utils.ai_utils.llm_clients import GroqProvider, OpenAIProvider, LLMService

def test_document(rfp_link: dict, session: requests.Session, llm: LLMService) -> bool:
    """
    Test what text is extracted from a document at the given url
    """
    try:
        fetch_html(rfp_link["parent_url"], session)
    except Exception as e:
        print(f"Error fetching HTML from parent URL: {e}")
        return {"message": str(e), "success": False}
    try:
        text = get_link_text(rfp_link, session)
        if ai_classify_rfp(text, llm):
            return {"message": "The text is an RFP", "success": True}
        else:
            return {"message": "The text is not an RFP", "success": False}
    except Exception as e:
        print(f"Error extracting text from document: {e}")
        return {"message": str(e), "success": False}

if __name__ == "__main__":
    session = requests.Session()
    rfp_link = {
        "url": "https://cms9files.revize.com/redcliffband/rfp/Document%20Center/Request%20for%20Proposals/Internet%20Service%20Provider%20Services%20RFP%2010.2025.pdf?t=202510301537330&t=202510301537330",
        "parent_url": "https://www.redcliff-nsn.gov/rfp/",
        "base_url": "https://www.redcliff-nsn.gov/rfp/",
        "href": "Document Center/Request for Proposals/2026 Confidentiality Audit RFP.pdf?t=202603121407330",
        "type": "pdf",
    }
    
    groq_client = Groq(api_key=GROQ_API_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    groq_provider = GroqProvider(groq_client)
    openai_provider = OpenAIProvider(openai_client)

    llm = LLMService(
        groq_provider,
        openai_provider,
        TokenTracker()
    )
    test_document(rfp_link, session, llm)