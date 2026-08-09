import sqlite3

from database import DB_PATH


# =========================================================
# ADD KNOWLEDGE TOPIC
# =========================================================

def add_topic(
    topic,
    content,
    detailed="",
    reference=""
):
    topic = (topic or "").strip()
    content = (content or "").strip()
    detailed = (detailed or "").strip()
    reference = (reference or "").strip()

    if not topic:
        raise ValueError("Topic is required")

    if not content and not detailed:
        raise ValueError("Content is required")

    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.cursor()

        # Check whether topic already exists
        cursor.execute(
            """
            SELECT id
            FROM knowledge
            WHERE LOWER(topic) = LOWER(?)
            """,
            (topic,)
        )

        existing = cursor.fetchone()

        if existing:

            cursor.execute(
                """
                UPDATE knowledge
                SET
                    content = ?,
                    detailed_content = ?,
                    reference = ?
                WHERE id = ?
                """,
                (
                    content,
                    detailed,
                    reference,
                    existing[0]
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO knowledge
                (
                    topic,
                    content,
                    type,
                    detailed_content,
                    reference
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    topic,
                    content,
                    "knowledge",
                    detailed,
                    reference
                )
            )

        conn.commit()

    finally:
        conn.close()

    return True


# =========================================================
# DASHBOARD STATISTICS
# =========================================================

def get_dashboard_stats():

    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM users"
        )
        users = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM chat_history"
        )
        chats = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM knowledge"
        )
        knowledge = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM feedback
            WHERE rating = 'helpful'
            """
        )
        helpful = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM feedback
            WHERE rating = 'not_helpful'
            """
        )
        not_helpful = cursor.fetchone()[0]

        return {
            "total_users": users,
            "total_chats": chats,
            "knowledge_topics": knowledge,
            "helpful_feedback": helpful,
            "not_helpful_feedback": not_helpful
        }

    finally:
        conn.close()


# =========================================================
# MOST ASKED QUESTIONS
# =========================================================

def get_most_asked_questions():

    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                question,
                COUNT(*) AS total
            FROM chat_history
            GROUP BY question
            ORDER BY total DESC
            LIMIT 10
            """
        )

        rows = cursor.fetchall()

        return [
            {
                "question": row[0],
                "count": row[1]
            }
            for row in rows
        ]

    finally:
        conn.close()
