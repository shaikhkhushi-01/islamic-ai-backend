from fastapi import APIRouter, Depends
import sqlite3

from database import DB_PATH
from auth import get_current_user

router = APIRouter()


@router.get("/history")
def history(current_user: dict = Depends(get_current_user)):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT question, answer
        FROM chat_history
        WHERE user_id=?
        ORDER BY id ASC
        """,
        (current_user["id"],)
    )

    rows = cursor.fetchall()

    conn.close()

    return {
        "history": [
            {
                "question": row[0],
                "answer": row[1]
            }
            for row in rows
        ]
    }


@router.delete("/clear")
def clear_chat(current_user: dict = Depends(get_current_user)):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM chat_history
        WHERE user_id=?
        """,
        (current_user["id"],)
    )

    conn.commit()
    conn.close()

    return {
        "message": "Chat cleared successfully"
    }
