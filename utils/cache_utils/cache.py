import hashlib
import psycopg

def hash_text(text: str) -> str:
    """
    Hash the text
    """
    return hashlib.sha256(text.encode()).hexdigest()

def has_document_changed(document_text: str, document_url: str, db_connection: psycopg.Connection) -> bool:
    """
    Check if the document has changed since the last time we scraped it
    """
    current_hash = hash_text(document_text)

    with db_connection.cursor() as cursor:
        cursor.execute("SELECT document_hash FROM documents WHERE document_url = %s", (document_url,))
        result = cursor.fetchone()
        if result:
            previous_hash = result[0]
        else:
            previous_hash = None

    return current_hash != previous_hash