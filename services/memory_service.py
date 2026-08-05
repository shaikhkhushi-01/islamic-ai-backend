import sqlite3
from difflib import get_close_matches

from database import DB_PATH


def save_memory(session_id, topic):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM chat_memory WHERE session_id=?",
        (session_id,)
    )

    cursor.execute(
        """
        INSERT INTO chat_memory(session_id,last_topic)
        VALUES(?,?)
        """,
        (
            session_id,
            topic
        )
    )

    conn.commit()
    conn.close()


def get_memory(session_id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT last_topic
        FROM chat_memory
        WHERE session_id=?
        """,
        (session_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if row:

        return row[0]

    return None


def get_related_topics(current_topic):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT topic,type
        FROM knowledge
        """
    )

    rows = cursor.fetchall()

    conn.close()

    current_type = None

    for topic, t in rows:

        if topic == current_topic:

            current_type = t

            break

    if current_type is None:

        return []

    topics = [

        topic

        for topic, t in rows

        if t == current_type and topic != current_topic

    ]

    similar = get_close_matches(

        current_topic,

        topics,

        n=8,

        cutoff=0.30

    )

    return similar
