from services.search_service import search_database
from rag_engine import semantic_search
from quran_engine import search_quran
from hadith_engine import search_hadith


def retrieve_context(user_msg, session_id):

    context = ""

    related = []

    topic = None

    # -----------------------------
    # Keyword Search
    # -----------------------------
    result = search_database(
        user_msg,
        session_id
    )

    if result:

        context += result["text"] + "\n\n"

        related = result["related"]

        topic = result["topic"]

    # -----------------------------
    # Semantic Search
    # -----------------------------
    semantic = semantic_search(user_msg)

    for item in semantic:

        context += (
            f"Topic: {item['topic']}\n"
            f"{item['text']}\n\n"
        )

    # -----------------------------
    # Quran Search
    # -----------------------------
    quran = search_quran(user_msg)

    if quran:

        context += "\n=== Quran ===\n"

        for verse in quran:

            context += (
                f"{verse['surah']} "
                f"({verse['ayah']})\n"
                f"{verse['text']}\n\n"
            )

    # -----------------------------
    # Hadith Search
    # -----------------------------
    hadith = search_hadith(user_msg)

    if hadith:

        context += "\n=== Hadith ===\n"

        for h in hadith:

            context += (
                f"{h['book']} "
                f"({h['number']})\n"
                f"{h['text']}\n\n"
            )

    return {

        "context": context,

        "related": related,

        "topic": topic

    }
