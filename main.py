import requests
import json
import os
from dotenv import load_dotenv

from utils.db_util import get_db_connection

from utils.scraping_utils import fetch_html, extract_rfp_links, get_link_text

from utils.pdf_utils import extract_pdf_text, download_pdf

from utils.ai_utils.llm_clients import GroqProvider, OpenAIProvider, LLMService
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


def main(db_connection, llm: LLMService, job_id: str = None):
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
        other_types_to_process = [] # Code is currently setup to process html and pdf links. Create an array to hold links of other types.
        rfps_to_process = [] # Will hold the dicts of links we determined to be RFPs

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

            ## TODO: Add step here to hash the page and check if it has changed since last time we scraped it
            
            ## Extract the RFP links from the tribe's page
            ## TODO: what if the rfps are listed out with no link?
            rfp_links = extract_rfp_links(html, tribe["rfp_url"], session)

            # For each link, get the text and determine if it is an RFP
            for rfp_link in rfp_links:
                print(rfp_link["title"], rfp_link["url"], rfp_link["type"])
                if rfp_link["type"] in ('html', 'pdf'): # Only process html and pdf links for right now
                    text = get_link_text(rfp_link, session)
                else:
                    print(f"Link {rfp_link['url']} is not an HTML or PDF page")
                    other_types_to_process.append(rfp_link) # make note of other types of links
                    continue
                if text is None: # If we failed to extract text, skip the link
                    print(f"Failed to extract text from the link for {rfp_link['title']}")
                    continue

                ## TODO: Add step here to hash the text of the rfp link and check if it has changed since last time we scraped it
                print(f"Successfully extracted the text from the link for {rfp_link['title']}")
                if ai_classify_rfp(text, llm):
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

            if len(rfp_links) == 0:
                print(f"No Candidate RFP links found for tribe {tribe['Tribe']}")
                continue

            # TODO: investigate the rfp link more to extract info about the rfp (title, description, deadline, project size)
            # TODO: categorize the rfp? Maybe do this at the same time as extracting the data?
    
        ### At this point we have a list of all the RFPs to process
        print(f"Found {len(rfps_to_process)} total RFPs to process across all tribes")

        print(f"Found {len(other_types_to_process)} other types of links to process")

        for other_type in other_types_to_process:
            print(f"Other type: {other_type}")

    except Exception as e:
        print(f"Error scraping the RFP pages for tribe {tribe['Tribe']}")
        print(f"Error scraping the RFP pages: {e}")
        return {"message": str(e), "stage": f"scraping rfp pages, tribe {tribe['Tribe']}", "success": False}
    finally:
        return {"message": "RFP pages scraped successfully", "stage": "scraping rfp pages", "success": True}



if __name__ == "__main__":
    db_connection = get_db_connection()

    groq_client = Groq(api_key=GROQ_API_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    groq_provider = GroqProvider(groq_client)
    openai_provider = OpenAIProvider(openai_client)

    llm = LLMService(
        groq_provider,
        openai_provider,
        TokenTracker()
    )
    main(db_connection, llm)
    db_connection.close()