import sqlite3
from datetime import datetime

from database import DB_PATH


def save_feedback(
    user_id,
    question,
    answer,
    rating
):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO feedback
        (
            user_id,
            question,
            answer,
            rating,
            created_at
        )
        VALUES(?,?,?,?,?)
        """,
        (
            user_id,
            question,
            answer,
            rating,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()
