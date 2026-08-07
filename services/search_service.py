import sqlite3
from difflib import get_close_matches

from database import DB_PATH
from ai_engine import detect_emotion
from services.ranking_service import rank_results
from rag_engine import semantic_search
from services.memory_service import (
    save_memory,
    get_memory,
    get_related_topics,
)


# ================= BEST MATCH =================

def find_best_match(user_msg, topics):

    user_msg = user_msg.lower()

    # Long topics first
    topics_sorted = sorted(topics, key=len, reverse=True)

    # Exact phrase match
    for topic in topics_sorted:
        if topic.lower() in user_msg:
            return topic

    words = user_msg.split()

    # Exact word match
    for word in words:
        if word in topics:
            return word

    # Fuzzy match
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


# ================= DATABASE SEARCH =================

def search_database(user_msg, session_id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    original_message = user_msg
    user_msg = user_msg.lower().strip()

    # ================= SYNONYMS =================

    synonyms = {
        "sad": "depression",
        "depressed": "depression",
        "lonely": "depression",

        "tension": "stress",
        "worried": "stress",
        "anxious": "stress",

        "traveling": "travel prayer",
        "travelling": "travel prayer",
        "journey": "travel prayer",

        "song": "music",
        "songs": "music",

        "pray": "prayer",
        "praying": "prayer",
        "namaz": "prayer",
    }

    for old, new in synonyms.items():
        if old in user_msg:
            user_msg = user_msg.replace(old, new)

    # ================= GET KNOWLEDGE =================

    cursor.execute(
        """
        SELECT
            topic,
            content,
            detailed_content,
            reference
        FROM knowledge
        """
    )

    rows = cursor.fetchall()

    # No database knowledge
    if not rows:
        conn.close()

        semantic = semantic_search(original_message)

        return {
            "topic": None,
            "text": semantic if semantic else "",
            "related": []
        }

    # ================= PREPARE RANKING =================

    results = []

    for topic, content, detailed, reference in rows:

        results.append({
            "topic": topic,
            "content": content,
            "detailed": detailed,
            "reference": reference
        })

    # Rank possible results
    ranked_results = rank_results(
        user_msg,
        results
    )

    topics = [row[0] for row in rows]

    # ================= TOPIC DETECTION =================

    if "music" in user_msg:
        best_topic = "music"

    elif "haram" in user_msg and "music" not in user_msg:
        best_topic = "haram"

    else:
        best_topic = find_best_match(
            user_msg,
            topics
        )

    # Ranking fallback
    if not best_topic and ranked_results:

        top_result = ranked_results[0]

        if isinstance(top_result, dict):
            best_topic = top_result.get("topic")

    # ================= FOUND TOPIC =================

    if best_topic:

        for topic, content, detailed, reference in rows:

            if topic == best_topic:

                save_memory(
                    session_id,
                    topic
                )

                reply = detailed if detailed else content

                if not reply:
                    reply = ""

                # Reference
                if reference:
                    reply += (
                        f"\n\n📖 Reference: {reference}"
                    )

                # ================= EMOTION =================

                emotion = detect_emotion(
                    original_message
                )

                if emotion == "sad":

                    reply += (
                        "\n\n🤲 Dua: "
                        "Allahumma inni a'udhu bika "
                        "minal-hammi wal-hazan."
                    )

                elif emotion == "anxiety":

                    reply += (
                        "\n\n📿 Zikr: "
                        "Hasbunallahu wa ni'mal wakeel."
                    )

                elif emotion == "guilt":

                    reply += (
                        "\n\n🕊 Tawbah: "
                        "Say Astaghfirullah sincerely "
                        "and turn back to Allah."
                    )

                elif emotion == "anger":

                    reply += (
                        "\n\n📜 Reminder: "
                        "Control anger and seek refuge "
                        "in Allah."
                    )

                related = get_related_topics(
                    topic
                )

                conn.close()

                return {
                    "topic": topic,
                    "text": reply,
                    "related": related
                }

    # ================= MEMORY FALLBACK =================

    last_topic = get_memory(
        session_id
    )

    if last_topic:

        cursor.execute(
            """
            SELECT
                content,
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

            reply = detailed if detailed else content

            if not reply:
                reply = ""

            if reference:
                reply += (
                    f"\n\n📖 Reference: {reference}"
                )

            conn.close()

            return {
                "topic": last_topic,
                "text": reply,
                "related": []
            }

    conn.close()

    # ================= SEMANTIC SEARCH FALLBACK =================

    semantic = semantic_search(
        original_message
    )

    return {
        "topic": None,
        "text": semantic if semantic else "",
        "related": []
    }


# ================= LAST TOPIC =================

def get_last_topic(session_id):

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
