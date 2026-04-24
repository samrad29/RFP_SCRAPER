import requests
import json
import os
from dotenv import load_dotenv

from utils.db_util import get_db_connection

from utils.scraping_utils import fetch_html, extract_rfp_links

from utils.pdf_utils import extract_pdf_text, download_pdf

from utils.ai_utils.llm_clients import GroqProvider, OpenAIProvider, LLMService, TokenTracker
from utils.ai_utils.prompts import ai_classify_rfp, ai_extract_rfp_data
from utils.ai_utils.llm_utils import TokenTracker

from groq import Groq
from openai import OpenAI

load_dotenv()
SHEETS_APP_URL = os.getenv("SHEETS_APP_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")

groq_client = Groq(GROQ_API_KEY)
openai_client = OpenAI(OPENAI_API_KEY)

groq_provider = GroqProvider(groq_client)
openai_provider = OpenAIProvider(openai_client)

llm = LLMService(
    groq_provider,
    openai_provider,
    TokenTracker()
)


def main(db_connection, job_id: str = None):
    ## Get the list of RFP pages from the spreadsheet


    session = requests.Session()
    try:
        response = requests.get(SHEETS_APP_URL).json()
        rfp_urls = response["data"]
    except Exception as e:
        print(f"Error getting the list of RFP pages from the spreadsheet: {e}")
        return {"message": str(e), "stage": "fetching urls from spreadsheet", "success": False}
    
    ## Scrape the RFP pages
    try:
        rfps_to_process = []
        for tribe in rfp_urls:
            if tribe["rfp_url"] == "None":
                print(f"No RFP URL found for tribe {tribe['Tribe']}, skipping")
                continue
            
            # Grab the html of the RFPs page
            html = fetch_html(tribe["rfp_url"], session)
            if html:
                print(f"Successfully fetched the HTML of the RFP page for {tribe['Tribe']}")
            else:
                print(f"Failed to fetch the HTML of the RFP page for {tribe['Tribe']}")
            
            ## Extract the RFP links from the page (assumes the page has a list of links to RFPs)
            rfp_links = extract_rfp_links(html, tribe["rfp_url"], session)
            for rfp_link in rfp_links:
                print(rfp_link["title"], rfp_link["url"], rfp_link["type"])
            if len(rfp_links) == 0:
                print(f"No Candidate RFP links found for tribe {tribe['Tribe']}")
                continue

            ## Extract the text from the RFP if it is a PDF
            rfp_text = []
            if rfp_link["type"] == "pdf":
                pdf_bytes = download_pdf(rfp_link["url"], session)
                if pdf_bytes:
                    pdf_text, method_used = extract_pdf_text(pdf_bytes)
                    if pdf_text:
                        rfp_text.append(pdf_text)
                        print(f"Successfully extracted the text from the PDF of the RFP for {rfp_link['title']}")
                    else:
                        print(f"Failed to extract text from the PDF of the RFP for {rfp_link['title']}")
                else:
                    print(f"Failed to download the PDF of the RFP for {rfp_link['title']}")


            for text in rfp_text:
                if ai_classify_rfp(text, groq_client, GROQ_MODEL_NAME):
                    print(f"The text is an RFP")
                    rfps_to_process.append({
                        "tribe": tribe["Tribe"],
                        "title": rfp_link["title"],
                        "url": rfp_link["url"],
                        "type": rfp_link["type"],
                        "text": text
                    })
                else:
                    print(f"The text is not an RFP")

    except Exception as e:
        print(f"Error scraping the RFP pages for tribe {tribe['Tribe']}")
        print(f"Error scraping the RFP pages: {e}")
        return {"message": str(e), "stage": f"scraping rfp pages, tribe {tribe['Tribe']}", "success": False}
    finally:
        return {"message": "RFP pages scraped successfully", "stage": "scraping rfp pages", "success": True}



if __name__ == "__main__":
    db_connection = get_db_connection()
    main(db_connection)
    db_connection.close()