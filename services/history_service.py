import sqlite3

from database import DB_PATH


def get_history(user_id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT question,answer
        FROM chat_history
        WHERE user_id=?
        ORDER BY id ASC
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


def clear_history(user_id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM chat_history
        WHERE user_id=?
        """,
        (user_id,)
    )

    conn.commit()

    conn.close()
