import os
import psycopg
from dotenv import load_dotenv

def get_db_connection(test_mode: bool = False):
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
                url TEXT,
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
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

            ## Create the RFP versions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS rfp_versions (
                rfp_version_id SERIAL PRIMARY KEY,
                rfp_id SERIAL NOT NULL REFERENCES rfps(rfp_id),
                version_hash TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                deadline DATE,
                link TEXT,
                categories TEXT, ## json array of strings
                project_size TEXT,
                attachments TEXT, ## json array of strings
                ai_summary TEXT,
                is_current BOOLEAN NOT NULL DEFAULT FALSE,
                change_summary TEXT,
                raw_text TEXT,
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
            conn.commit()

    except Exception as e:
        print(f"Error initializing the database: {e}")
        raise RuntimeError(f"Error initializing the database: {e}")
    finally:
        conn.close()

def reset_db(conn):
    """
    Reset the database
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            DROP TABLE IF EXISTS rfp_scraper_jobs, sources, documents, rfps, rfp_versions
            """)
            conn.commit()
    except Exception as e:
        print(f"Error resetting the database: {e}")
        raise RuntimeError(f"Error resetting the database: {e}")