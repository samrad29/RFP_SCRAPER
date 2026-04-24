import requests
import json
import os
from dotenv import load_dotenv

from db_util import get_db_connection

from scraping_utils import fetch_html, extract_rfp_links

from pdf_utils import extract_pdf_text, download_pdf

def main(db_connection, job_id: str = None):
    ## Get the list of RFP pages from the spreadsheet
    load_dotenv()
    SHEETS_APP_URL = os.getenv("SHEETS_APP_URL")

    session = requests.Session()
    try:
        response = requests.get(SHEETS_APP_URL).json()
        rfp_urls = response["data"]
    except Exception as e:
        print(f"Error getting the list of RFP pages from the spreadsheet: {e}")
        return {"message": str(e), "stage": "fetching urls from spreadsheet", "success": False}
    
    ## Scrape the RFP pages
    try:
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
            if rfp_link["type"] == "pdf":
                pdf_bytes = download_pdf(rfp_link["url"], session)
                if pdf_bytes:
                    pdf_text, method_used = extract_pdf_text(pdf_bytes)
                    if pdf_text:
                        print(f"Successfully extracted the text from the PDF of the RFP for {rfp_link['title']}")
                    else:
                        print(f"Failed to extract the text from the PDF of the RFP for {rfp_link['title']}")
                else:
                    print(f"Failed to download the PDF of the RFP for {rfp_link['title']}")
            
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