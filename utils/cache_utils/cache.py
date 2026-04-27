import hashlib
import psycopg

def hash_text(text: str) -> str:
    """
    Hash the text
    """
    return hashlib.sha256(text.encode()).hexdigest()

def has_document_changed(source_id: int, document_text: str, document_url: str, db_connection: psycopg.Connection) -> bool:
    """
    Check if the document has changed since the last time we scraped it
    """
    current_hash = hash_text(document_text)

    with db_connection.cursor() as cursor:
        cursor.execute("SELECT document_hash FROM documents WHERE source_id = %s AND document_url = %s", (source_id, document_url))
        result = cursor.fetchone()
        if result:
            previous_hash = result[0]
        else:
            previous_hash = None

    return current_hash != previous_hash

def cache_document(rfp_link: dict, source_id: int, db_connection: psycopg.Connection):
    """
    Cache the document (upsert by source_id + document_url).
    Uses Tries to update the document, if it fails, it inserts the document.
    """
    try:
        current_hash = hash_text(rfp_link["text"])
        document_url = rfp_link["url"]
        document_type = rfp_link["type"]
        document_base_url = rfp_link["base_url"]
        document_href = rfp_link["href"]
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE documents SET
                    document_base_url = %s,
                    document_href = %s,
                    document_hash = %s,
                    document_type = %s,
                    updated_at = CURRENT_TIMESTAMP,
                    active = TRUE
                WHERE source_id = %s AND document_url = %s
                """,
                (
                    document_base_url,
                    document_href,
                    current_hash,
                    document_type,
                    source_id,
                    document_url,
                ),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    """
                    INSERT INTO documents (
                        source_id, document_url, document_base_url, document_href,
                        document_hash, document_type
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        source_id,
                        document_url,
                        document_base_url,
                        document_href,
                        current_hash,
                        document_type,
                    ),
                )
            db_connection.commit()
    except Exception as e:
        print(f"Error caching the document: {e}")
        raise RuntimeError(f"Error caching the document: {e}")

def get_cached_rfp_links(source_id: int, db_connection: psycopg.Connection):
    """
    Get the cached RFP links
    """
    try:
        with db_connection.cursor() as cursor:
            cursor.execute(
                "SELECT document_url, document_base_url, document_href, document_type FROM documents WHERE source_id = %s and active = true",
                (source_id,),
            )
            result = cursor.fetchall()
            return [
                {
                    "title": "",
                    "url": row[0],
                    "base_url": row[1],
                    "href": row[2],
                    "type": row[3],
                }
                for row in result
            ]
    except Exception as e:
        print(f"Error getting the cached RFP links: {e}")
        raise RuntimeError(f"Error getting the cached RFP links: {e}")

def cache_source(source_url: str, tribe_name: str, html: str, db_connection: psycopg.Connection):
    """
    Cache the source
    """
    try:
        with db_connection.cursor() as cursor:
            current_hash = hash_text(html)
            cursor.execute("SELECT hash, source_id FROM sources WHERE source_url = %s AND tribe_name = %s", (source_url, tribe_name))
            result = cursor.fetchone()
            if result and result[0] is not None and result[0] == current_hash:
                print(f"Source for {tribe_name} has not changed, returning cached version")
                return {"new": False, "source_id": result[1]}    
            else:
                print(f"Source for {tribe_name} is new or has changed, caching it")
            if result: # source already exists, update the hash
                cursor.execute(
                    "UPDATE sources SET hash = %s, updated_at = CURRENT_TIMESTAMP WHERE source_id = %s",
                    (current_hash, result[1]),
                )
                db_connection.commit()
                source_id = result[1]
            else: # source does not exist, create it
                cursor.execute("INSERT INTO sources (source_url, tribe_name, hash) VALUES (%s, %s, %s)", (source_url, tribe_name, current_hash))
                db_connection.commit()
                cursor.execute("SELECT source_id FROM sources WHERE source_url = %s AND tribe_name = %s", (source_url, tribe_name))
                result = cursor.fetchone()
                source_id = result[0] if result else None
        print(f"Cached the source for {tribe_name} with ID: {source_id}")
        return {"new": True, "source_id": source_id}
    except Exception as e:
        print(f"Error caching the source: {e}")
        raise RuntimeError(f"Error caching the source: {e}")