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
from services.prompt_service import build_prompt

from utils.logger import logger


def process_chat(user_msg, current_user):

    # =========================
    # Query Rewrite
    # =========================

    user_msg = rewrite_query(user_msg)

    # =========================
    # Greeting
    # =========================

    greeting = handle_greeting(user_msg)

    if greeting:
        return {
            "reply": greeting,
            "related_topics": [],
            "references": [],
            "confidence": "100%",
            "source": "Greeting Engine"
        }

    # =========================
    # Quran Search
    # =========================

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
            "confidence": "100%",
            "source": "Quran Engine"
        }

    # =========================
    # Hadith Search
    # =========================

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
            "confidence": "100%",
            "source": "Hadith Engine"
        }

    # =========================
    # Logging
    # =========================

    logger.info(f"Question : {user_msg}")

    session_id = str(current_user["id"])

    # =========================
    # Follow-up Detection
    # =========================

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
        r"^it's",
        r"^their",
        r"^them",
        r"^that",
        r"^this",
        r"^those",
        r"^these"
    ]

    is_follow_up = any(
        re.match(pattern, user_msg.lower())
        for pattern in follow_up_patterns
    )

    # =========================
    # Retrieval
    # =========================

    retrieval = retrieve_context(
        user_msg,
        session_id
    )

    context = retrieval.get("context", "")
    related = retrieval.get("related", [])
    topic = retrieval.get("topic")

    # =========================
    # Fallback Database Search
    # =========================

    if not context:

        result = search_database(
            user_msg,
            session_id
        )

        if result:

            context = result.get("text", "")
            related = result.get("related", [])
            topic = result.get("topic")

    # =========================
    # Semantic Search Fallback
    # =========================

    if not context:

        semantic = semantic_search(user_msg)

        if semantic:

            if isinstance(semantic, str):
                context = semantic
                related = []
                topic = None

            elif isinstance(semantic, list):

                context_parts = []

                for item in semantic:

                    if isinstance(item, dict):

                        item_topic = item.get("topic", "")
                        item_text = item.get("text", "")

                        context_parts.append(
                            f"Topic: {item_topic}\n"
                            f"{item_text}"
                        )

                context = "\n\n".join(context_parts)

                if semantic and isinstance(semantic[0], dict):
                    topic = semantic[0].get("topic")

                related = []

    # =========================
    # No Knowledge Found
    # =========================

    if not context:

        return {
            "reply": (
                "Sorry, I couldn't find authentic Islamic knowledge "
                "related to your question."
            ),
            "related_topics": [],
            "references": [],
            "confidence": "20%",
            "source": "Knowledge Base"
        }

    # =========================
    # Context Validation
    # =========================

    if not has_enough_context(context):

        return {
            "reply": (
                "Sorry, I couldn't find enough authentic "
                "Islamic evidence to answer this question."
            ),
            "related_topics": related,
            "references": [],
            "confidence": "20%",
            "source": "Knowledge Base"
        }

    # =========================
    # Prompt Engineering
    # =========================

    prompt = build_prompt(
        user_msg,
        context
    )

    # =========================
    # AI Response
    # =========================

    reply = ask_groq(prompt)

    # =========================
    # Hallucination / Safety Guard
    # =========================

    if not validate_response(reply):

        reply = (
            "Sorry, I couldn't verify this response "
            "from authentic Islamic sources."
        )

    logger.info(f"Answer : {reply}")

    # =========================
    # Citation
    # =========================

    reference = ""

    if topic:
        reference = get_reference(topic)

    # =========================
    # Confidence
    # =========================

    confidence = calculate_confidence(context)

    # =========================
    # Save Chat History
    # =========================

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

    # =========================
    # Final Response
    # =========================

    return {
        "reply": reply,
        "related_topics": related,
        "reference": reference,
        "confidence": confidence,
        "source": context[:150]
    }
