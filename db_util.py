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
        return psycopg.connect(database_url)
    else: 
        raise RuntimeError("DATABASE_URL is not set")