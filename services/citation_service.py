import sqlite3
from database import DB_PATH


def get_reference(topic):

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

    conn.close()

    if row and row[0]:
        return row[0]

    return None
