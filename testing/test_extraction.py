
from utils.scraping_utils import get_link_text
import requests
from utils.ai_utils.prompts import ai_extract_rfp_data
from utils.ai_utils.llm_utils import TokenTracker
from utils.scraping_utils import fetch_html
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
        if "parent_url" in rfp_link:
            fetch_html(rfp_link["parent_url"], session)
    except Exception as e:
        print(f"Error fetching HTML from parent URL: {e}")
        return {"message": "Failed to fetch HTML from parent URL", "success": False}
    try:
        text = get_link_text(rfp_link, session)
        if text is None:
            return {"message": "Failed to extract text from document", "success": False}
    except Exception as e:
        print(f"Error extracting text from document: {e}")
        return {"message": str(e), "success": False}
    try:
        rfp_data = ai_extract_rfp_data(text, llm)
        print(f"RFP data: {rfp_data}")
        return {"message": "RFP data extracted successfully", "success": True, "rfp_data": rfp_data}
    except Exception as e:   
        print(f"Error extracting RFP data: {e}")
        return {"message": str(e), "success": False}

if __name__ == "__main__":
    session = requests.Session()
    rfp_link = {
        "url": "https://www.menominee-nsn.gov/ViewDocument.aspx?RFPid=64",
        "parent_url": "https://www.menominee-nsn.gov/BusinessPages/RequestForProposals",
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