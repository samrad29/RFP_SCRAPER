import requests
import json
import os
from dotenv import load_dotenv
from db_util import get_db_connection

from scraping_utils import fetch_html


def main(db_connection, job_id: str):
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
            html = fetch_html(tribe["rfp_url"], session)

            if html:
                print(f"Successfully scraped the RFP page for {tribe['Tribe']}")
            else:
                print(f"Failed to scrape the RFP page for {tribe['Tribe']}")
    except Exception as e:
        print(f"Error scraping the RFP pages for tribe {tribe['Tribe']}")
        print(f"Error scraping the RFP pages: {e}")
        return {"message": str(e), "stage": f"scraping rfp pages, tribe {tribe['Tribe']}", "success": False}
    finally:
        return {"message": "RFP pages scraped successfully", "stage": "scraping rfp pages", "success": True}



if __name__ == "__main__":
    db_connection = get_db_connection()
    main(db_connection)