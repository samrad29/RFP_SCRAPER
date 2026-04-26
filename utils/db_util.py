import os
import psycopg
from dotenv import load_dotenv

def get_db_connection():
    """
    Get a connection to the database
    """
    load_dotenv()
    database_url = (os.getenv("DB_URL") or "").strip()
    if database_url:
        if psycopg is None:
            raise RuntimeError("psycopg is required for DATABASE_URL connections.")
        print("Connecting to Postgres via DATABASE_URL")
        conn = psycopg.connect(database_url)
        initialize_db(conn)
        return conn
    else: 
        raise RuntimeError("DATABASE_URL is not set")

def initialize_db(conn):
    """
    Initialize the database
    """
    try:
        with conn.cursor() as cursor:
            ## Create the rfp_scraper_jobs table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS rfp_scraper_jobs (
                id SERIAL PRIMARY KEY,
                job_id VARCHAR(255) NOT NULL,
                status VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                new_rfps_count INT NOT NULL,
                updated_rfps_count INT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            ## Create the sources table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                source_id SERIAL PRIMARY KEY,
                tribe_name VARCHAR(255) NOT NULL,
                source_url TEXT,
                status TEXT,
                status_message TEXT,
                rfp_url TEXT,
                scrape_type TEXT,
                hash TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            ## Create the documents table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id SERIAL PRIMARY KEY,
                source_id INT NOT NULL REFERENCES sources(source_id),
                document_type TEXT NOT NULL,
                document_url TEXT NOT NULL,
                document_hash TEXT NOT NULL,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            ## Create an RFP table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS rfps (
                rfp_id SERIAL PRIMARY KEY,
                source_id INT NOT NULL REFERENCES sources(source_id),
                title TEXT NOT NULL,
                hash TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            ## Create the RFP versions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS rfp_versions (
                rfp_version_id SERIAL PRIMARY KEY,
                rfp_id INTEGER NOT NULL REFERENCES rfps(rfp_id),
                version_hash TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                deadline DATE,
                link TEXT,
                categories TEXT,
                project_size TEXT,
                attachments TEXT,
                ai_summary TEXT,
                is_current BOOLEAN NOT NULL DEFAULT FALSE,
                change_summary TEXT,
                raw_text TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            conn.commit()

    except Exception as e:
        print(f"Error initializing the database: {e}")
        raise RuntimeError(f"Error initializing the database: {e}")
    finally:
        pass


def update_source_status(tribe_name: str, status: str, message: str, db_connection: psycopg.Connection):
    """
    Update the status of the source
    """
    try:
        with db_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE sources SET status = %s, status_message = %s WHERE tribe_name = %s",
                (status, message, tribe_name),
            )
            db_connection.commit()
    except Exception as e:
        print(f"Error updating the status of the source: {e}")
        raise RuntimeError(f"Error updating the status of the source: {e}")

def get_source_status(tribe_name: str, db_connection: psycopg.Connection):
    """
    Get the status of the source
    """
    try:
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT status FROM sources WHERE tribe_name = %s", (tribe_name,))
            result = cursor.fetchone()
            return result
    except Exception as e:
        print(f"Error getting the status of the source: {e}")
        raise RuntimeError(f"Error getting the status of the source: {e}")

def update_document_active(source_id: int, document_urls: list[str], db_connection: psycopg.Connection):
    """
    Update the active status of the documents
    """
    try:
        with db_connection.cursor() as cursor:
            cursor.execute("UPDATE documents SET active = false WHERE source_id = %s AND document_url NOT IN (%s)", (source_id, document_urls))
            db_connection.commit()
    except Exception as e:
        print(f"Error updating the active status of the documents: {e}")

###### Posting to excel looks like this: data = [
#     {
#         "tribe_name": "Menominee",
#         "title": "IT Upgrade",
#         "due_date": "2026-05-01"
#     }
# ]