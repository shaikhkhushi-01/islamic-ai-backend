import re


def extract_references(text: str):

    references = []

    quran = re.findall(
        r"Quran\s*\d+:\d+",
        text,
        re.IGNORECASE
    )

    hadith = re.findall(
        r"(Sahih Bukhari|Sahih Muslim|Abu Dawood|Tirmidhi)\s*\d+",
        text,
        re.IGNORECASE
    )

    references.extend(quran)
    references.extend(hadith)

    return list(set(references))


def get_reference(topic: str):

    if not topic:
        return ""

    conn = None

    try:
        import sqlite3
        from database import DB_PATH

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT reference
            FROM knowledge
            WHERE topic=?
            """,
            (topic,)
        )

        row = cursor.fetchone()

        if row and row[0]:
            return row[0]

        return ""

    except Exception:
        return ""

    finally:
        if conn:
            conn.close()
