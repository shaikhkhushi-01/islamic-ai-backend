import sqlite3

from database import DB_PATH


def get_dashboard_stats():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total Users
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    # Total Chats
    cursor.execute("SELECT COUNT(*) FROM chat_history")
    chats = cursor.fetchone()[0]

    # Total Knowledge
    cursor.execute("SELECT COUNT(*) FROM knowledge")
    knowledge = cursor.fetchone()[0]

    # Helpful Feedback
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM feedback
        WHERE rating='helpful'
        """
    )
    helpful = cursor.fetchone()[0]

    # Not Helpful Feedback
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM feedback
        WHERE rating='not_helpful'
        """
    )
    not_helpful = cursor.fetchone()[0]

    conn.close()

    return {
        "total_users": users,
        "total_chats": chats,
        "knowledge_topics": knowledge,
        "helpful_feedback": helpful,
        "not_helpful_feedback": not_helpful
    }
