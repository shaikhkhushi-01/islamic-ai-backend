import sqlite3
from difflib import get_close_matches

from database import DB_PATH
from ai_engine import detect_emotion


# ================= MEMORY =================

def save_memory(session_id, topic):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM chat_memory WHERE session_id=?",
        (session_id,)
    )

    cursor.execute(
        "INSERT INTO chat_memory(session_id,last_topic) VALUES(?,?)",
        (session_id, topic)
    )

    conn.commit()
    conn.close()


def get_memory(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT last_topic FROM chat_memory WHERE session_id=?",
        (session_id,)
    )

    row = cursor.fetchone()

    conn.close()

    return row[0] if row else None


# ================= RELATED =================

def get_related_topics(current_topic):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT topic,type FROM knowledge")

    rows = cursor.fetchall()

    conn.close()

    current_type = None

    for topic, type_ in rows:
        if topic == current_topic:
            current_type = type_
            break

    if current_type is None:
        return []

    topics = [
        topic
        for topic, type_ in rows
        if type_ == current_type and topic != current_topic
    ]

    return get_close_matches(
        current_topic,
        topics,
        n=4,
        cutoff=0.3
    )


# ================= MATCH =================

def find_best_match(user_msg, topics):

    user_msg = user_msg.lower()

    topics = sorted(
        topics,
        key=len,
        reverse=True
    )

    for topic in topics:
        if topic.lower() in user_msg:
            return topic

    words = user_msg.split()

    for word in words:
        if word in topics:
            return word

    for word in words:

        match = get_close_matches(
            word,
            topics,
            n=1,
            cutoff=0.75
        )

        if match:
            return match[0]

    return None


# ================= SEARCH =================

def search_database(user_msg, session_id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    user_msg = user_msg.lower()

    synonyms = {

        "sad":"depression",
        "depressed":"depression",
        "stress":"stress",
        "tension":"stress",
        "journey":"travel prayer",
        "traveling":"travel prayer",
        "song":"music",
        "songs":"music",
        "pray":"prayer",
        "praying":"prayer",
        "namaz":"prayer"

    }

    for key,value in synonyms.items():
        user_msg = user_msg.replace(key,value)

    cursor.execute("""

    SELECT
    topic,
    content,
    detailed_content,
    reference

    FROM knowledge

    """)

    rows = cursor.fetchall()

    topics = [r[0] for r in rows]

    best_topic = find_best_match(user_msg, topics)

    if best_topic:

        for topic,content,detailed,reference in rows:

            if topic == best_topic:

                save_memory(session_id,topic)

                reply = detailed if detailed else content

                if reference:
                    reply += f"\n\n📖 Reference: {reference}"

                emotion = detect_emotion(user_msg)

                if emotion=="sad":
                    reply += "\n\n🤲 Dua: Allahumma inni a'udhu bika minal hammi wal hazan."

                elif emotion=="anxiety":
                    reply += "\n\n📿 Zikr: Hasbunallahu wa ni'mal wakeel."

                elif emotion=="guilt":
                    reply += "\n\n🕊 Tawbah: Astaghfirullah."

                elif emotion=="anger":
                    reply += "\n\n📜 Control anger for Allah."

                related = get_related_topics(topic)

                conn.close()

                return {
                    "text":reply,
                    "related":related
                }

    last = get_memory(session_id)

    if last:

        cursor.execute("""

        SELECT
        content,
        detailed_content,
        reference

        FROM knowledge

        WHERE topic=?

        """,(last,))

        row = cursor.fetchone()

        if row:

            content,detailed,reference = row

            conn.close()

            return {

                "text": detailed if detailed else content,

                "related":[]
            }

    conn.close()

    return None
