import sqlite3
from datetime import datetime

from database import DB_PATH
from services.search_service import search_database
from ai_engine import ask_groq
from utils.logger import logger


def process_chat(user_msg, current_user):

    logger.info(f"Question : {user_msg}")

    session_id = str(current_user["id"])

    result = search_database(
        user_msg,
        session_id
    )

    context = result["text"]
    related = result["related"]

    reply = ask_groq(
        user_msg,
        context
    )

    logger.info(f"Answer : {reply}")

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chat_history
        (
            user_id,
            question,
            answer,
            intent,
            created_at
        )
        VALUES(?,?,?,?,?)
        """,
        (
            current_user["id"],
            user_msg,
            reply,
            "knowledge",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()

    return {
        "reply": reply,
        "related_topics": related,
        "source": context[:150]
    }
