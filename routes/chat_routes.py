import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends

from database import DB_PATH
from auth import get_current_user

from models.schemas import Message

from services.search_service import search_database

from rag_engine import semantic_search

from ai_engine import (
    ask_groq,
    handle_greeting
)

from langdetect import detect

router = APIRouter()

def detect_language(text):

    try:

        lang = detect(text)

        if lang == "ur":
            return "urdu"

        elif lang == "ar":
            return "arabic"

        else:
            return "english"

    except:

        return "english"

@router.post("/chat")
def chat(
    data: Message,
    current_user: dict = Depends(get_current_user)
):

    user_msg = data.message.strip()

    if not user_msg:

        return {
            "reply": "Please ask something meaningful."
        }

    greeting = handle_greeting(user_msg)

    if greeting:

        return {

            "reply": greeting,

            "related_topics": []

        }

    session_id = str(current_user["id"])

    result = search_database(
        user_msg,
        session_id
    )

    if result:

        context = result["text"]

        related = result["related"]

    else:

        semantic = semantic_search(user_msg)

        if semantic:

            context = semantic[:4000]

        else:

            context = "No Islamic knowledge found."

        related = []

    reply = ask_groq(
        user_msg,
        context
    )

    language = detect_language(user_msg)

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

        "language": language,

        "related_topics": related,

        "source": context[:120]

    }
