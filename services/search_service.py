import sqlite3
from difflib import get_close_matches

from database import DB_PATH
from ai_engine import detect_emotion
from services.memory_service import (
    save_memory,
    get_memory,
    get_related_topics
)


def find_best_match(user_msg, topics):

    user_msg = user_msg.lower()

    topics_sorted = sorted(
        topics,
        key=len,
        reverse=True
    )

    for topic in topics_sorted:

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


def search_database(user_msg, session_id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    user_msg = user_msg.lower()

    synonyms = {

        "sad": "depression",
        "depressed": "depression",

        "tension": "stress",
        "worried": "stress",

        "traveling": "travel prayer",
        "journey": "travel prayer",

        "song": "music",
        "songs": "music",

        "pray": "prayer",
        "praying": "prayer",
        "namaz": "prayer"

    }

    for word, replacement in synonyms.items():

        if word in user_msg:
            user_msg = user_msg.replace(
                word,
                replacement
            )

    cursor.execute(
        """
        SELECT topic,
               content,
               detailed_content,
               reference
        FROM knowledge
        """
    )

    rows = cursor.fetchall()

    topics = [row[0] for row in rows]

    if "music" in user_msg:

        best_topic = "music"

    elif "haram" in user_msg and "music" not in user_msg:

        best_topic = "haram"

    else:

        best_topic = find_best_match(
            user_msg,
            topics
        )

    if best_topic:

        for topic, content, detailed, reference in rows:

            if topic == best_topic:

                save_memory(
                    session_id,
                    topic
                )

                reply = detailed if detailed else content

                if reference:

                    reply += (
                        f"\n\n📖 Reference: {reference}"
                    )

                emotion = detect_emotion(user_msg)

                if emotion == "sad":

                    reply += (
                        "\n\n🤲 Dua: Allahumma inni "
                        "a'udhu bika minal-hammi "
                        "wal-hazan."
                    )

                elif emotion == "anxiety":

                    reply += (
                        "\n\n📿 Zikr: "
                        "Hasbunallahu wa ni'mal wakeel."
                    )

                elif emotion == "guilt":

                    reply += (
                        "\n\n🕊 Tawbah:"
                        " Astaghfirullah sincerely."
                    )

                elif emotion == "anger":

                    reply += (
                        "\n\n📜 Hadith:"
                        " Strong believer controls anger."
                    )

                conn.close()

                return {

                    "text": reply,

                    "related": get_related_topics(topic)

                }

    last_topic = get_memory(session_id)

    if last_topic:

        cursor.execute(

            """
            SELECT content,
                   detailed_content,
                   reference
            FROM knowledge
            WHERE topic=?
            """,

            (last_topic,)

        )

        row = cursor.fetchone()

        if row:

            content, detailed, reference = row

            conn.close()

            return {

                "text": detailed if detailed else content,

                "related": []

            }

    conn.close()

    return None
