import sqlite3
import re
from rapidfuzz import fuzz

from database import DB_PATH


# =========================================================
# LIGHTWEIGHT RAG ENGINE
# =========================================================

index = None
texts = []


def normalize_text(text):
    """
    Normalize text for lightweight semantic matching.
    """

    if not text:
        return ""

    text = text.lower()

    text = re.sub(
        r"[^\w\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def get_words(text):
    return set(
        normalize_text(text).split()
    )


def calculate_score(query, text):

    query_words = get_words(query)
    text_words = get_words(text)

    if not query_words or not text_words:
        return 0

    # Word overlap
    overlap = len(
        query_words.intersection(text_words)
    )

    overlap_score = (
        overlap / len(query_words)
    ) * 100

    # Fuzzy similarity
    fuzzy_score = fuzz.token_set_ratio(
        query,
        text
    )

    # Combined score
    score = (
        overlap_score * 0.65
        +
        fuzzy_score * 0.35
    )

    return score


def build_index():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT topic,
               detailed_content,
               content
        FROM knowledge
        """
    )

    rows = cursor.fetchall()

    conn.close()

    chunks = []

    CHUNK_SIZE = 700

    for topic, detailed, content in rows:

        text = detailed if detailed else content

        if not text:
            continue

        text = str(text)

        for i in range(
            0,
            len(text),
            CHUNK_SIZE
        ):

            chunk = text[
                i:i + CHUNK_SIZE
            ]

            if not chunk.strip():
                continue

            chunks.append(
                {
                    "topic": topic,
                    "text": chunk
                }
            )

    return None, chunks


def initialize_rag():

    global index
    global texts

    if not texts:

        index, texts = build_index()

    return index, texts


def semantic_search(query):

    global index
    global texts

    if not texts:

        initialize_rag()

    if not texts:

        return []

    scored_results = []

    for item in texts:

        score = calculate_score(
            query,
            item["text"]
        )

        if score <= 0:
            continue

        scored_results.append(
            (
                score,
                item
            )
        )

    scored_results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # Return top 3 results
    results = [
        item
        for score, item
        in scored_results[:3]
    ]

    return results


def refresh_index():

    global index
    global texts

    index = None
    texts = []

    initialize_rag()
