from db_util import get_db_connection

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
    
if __name__ == "__main__":
    conn = get_db_connection()
    reset_db(conn)
    conn.close()