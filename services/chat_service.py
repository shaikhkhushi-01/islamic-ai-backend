import sqlite3
from datetime import datetime

from database import DB_PATH
from rag_engine import semantic_search
from ai_engine import ask_groq
from utils.search import search_database


def chat_response(user_msg, current_user):

    session_id = str(current_user["id"])

    result = search_database(user_msg, session_id)

    if result:

        context = result["text"]
        related = result["related"]

    else:

        context = semantic_search(user_msg)

        related = []

    reply = ask_groq(user_msg, context)

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chat_history
        (user_id,question,answer,intent,created_at)

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
