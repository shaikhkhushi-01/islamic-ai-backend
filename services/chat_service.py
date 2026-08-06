import sqlite3
from datetime import datetime

from database import DB_PATH
from services.search_service import search_database
from ai_engine import ask_groq, handle_greeting
from hadith_engine import search_hadith
from quran_engine import search_quran
from services.citation_service import extract_references
from utils.logger import logger


def process_chat(user_msg, current_user):

    # Greeting
    greeting = handle_greeting(user_msg)

    if greeting:
        return {
            "reply": greeting,
            "related_topics": [],
            "source": "Greeting Engine"
        }

    # Quran Search
    quran_results = search_quran(user_msg)

    if quran_results:

        verses = ""

        for verse in quran_results:
            verses += (
                f"📖 {verse['surah']} ({verse['ayah']})\n"
                f"{verse['text']}\n\n"
            )

        return {
            "reply": verses,
            "related_topics": [],
            "references": [],
            "source": "Quran Engine"
        }

    # Hadith Search
    hadith_results = search_hadith(user_msg)

    if hadith_results:

        response = ""

        for hadith in hadith_results:
            response += (
                f"📜 {hadith['book']} ({hadith['number']})\n"
                f"{hadith['text']}\n\n"
            )

        return {
            "reply": response,
            "related_topics": [],
            "references": [],
            "source": "Hadith Engine"
        }

    logger.info(f"Question : {user_msg}")

    session_id = str(current_user["id"])

    result = search_database(user_msg, session_id)

    if not result:
        return {
            "reply": "Sorry, I couldn't find authentic Islamic knowledge related to your question.",
            "related_topics": [],
            "references": [],
            "source": "Knowledge Base"
        }

    context = result["text"]
    related = result["related"]

    reply = ask_groq(user_msg, context)

    logger.info(f"Answer : {reply}")

    # Extract Quran/Hadith references from AI reply
    references = extract_references(reply)

    # Save chat history
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
        "references": references,
        "source": context[:150]
    }
