import sqlite3
import re
from datetime import datetime

from database import DB_PATH

from ai_engine import (
    ask_groq,
    handle_greeting
)

from hadith_engine import search_hadith
from quran_engine import search_quran
from rag_engine import semantic_search

from services.query_service import rewrite_query
from services.search_service import (
    search_database,
    get_last_topic
)

from services.citation_service import get_reference
from services.confidence_service import calculate_confidence
from services.context_service import has_enough_context
from services.safety_service import validate_response
from services.retrieval_service import retrieve_context

from utils.logger import logger

def process_chat(user_msg, current_user):

    user_msg = rewrite_query(user_msg)

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

    follow_up_patterns = [
    r"^how many",
    r"^why",
    r"^how",
    r"^when",
    r"^where",
    r"^tell me more",
    r"^explain more",
    r"^what about",
    r"^its",
    r"^their",
    r"^them"
]

is_follow_up = any(
    re.match(pattern, user_msg.lower())
    for pattern in follow_up_patterns
)

    retrieval = retrieve_context(
    user_msg,
    session_id
)

context = retrieval["context"]

related = retrieval["related"]

topic = retrieval["topic"]
    topic = result["topic"]

else:

    semantic = semantic_search(user_msg)

    if not semantic:

        return {
            "reply": "Sorry, I couldn't find authentic Islamic knowledge related to your question.",
            "related_topics": [],
            "references": [],
            "source": "Knowledge Base"
        }

    context = ""

    for item in semantic:

        context += (
            f"Topic: {item['topic']}\n"
            f"{item['text']}\n\n"
        )

    related = []
    topic = semantic[0]["topic"]

if not has_enough_context(context):

    return {
        "reply": (
            "Sorry, I couldn't find enough authentic "
            "Islamic evidence to answer this question."
        ),
        "related_topics": [],
        "reference": "",
        "confidence": "20%",
        "source": "Knowledge Base"
    }

reply = ask_groq(
    user_msg,
    context
)

if not validate_response(reply):

    reply = (
        "Sorry, I couldn't verify this response "
        "from authentic Islamic sources."
    )

    logger.info(f"Answer : {reply}")

    # Extract Quran/Hadith references from AI reply
    reference = get_reference(topic)
    confidence = calculate_confidence(context)

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

    "reference": reference,

    "confidence": confidence,

    "source": context[:150]

}
