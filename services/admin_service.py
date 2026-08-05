import sqlite3

from database import DB_PATH
from rag_engine import refresh_index


def add_topic(topic, content, detailed, reference):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO knowledge
        (topic,content,type,detailed_content,reference)

        VALUES(?,?,?,?,?)
        """,
        (
            topic,
            content,
            "general",
            detailed,
            reference
        )
    )

    conn.commit()

    conn.close()

    refresh_index()

    return True
