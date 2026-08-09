import sqlite3
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from database import DB_PATH


model = None
index = None
texts = []


def get_model():
    global model

    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")

    return model


def build_index():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT topic, detailed_content, content
        FROM knowledge
        """
    )

    rows = cursor.fetchall()
    conn.close()

    chunks = []

    CHUNK_SIZE = 500

    for topic, detailed, content in rows:

        text = detailed if detailed else content

        if not text:
            continue

        for i in range(0, len(text), CHUNK_SIZE):

            chunk = text[i:i + CHUNK_SIZE]

            chunks.append({
                "topic": topic,
                "text": chunk
            })

    if not chunks:
        return None, []

    embedding_model = get_model()

    texts_only = [item["text"] for item in chunks]

    embeddings = embedding_model.encode(
        texts_only,
        convert_to_numpy=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    new_index = faiss.IndexFlatL2(
        embeddings.shape[1]
    )

    new_index.add(embeddings)

    return new_index, chunks


def initialize_rag():

    global index
    global texts

    if index is None:

        index, texts = build_index()

    return index, texts


def semantic_search(query):

    global index
    global texts

    if index is None:

        initialize_rag()

    if index is None or not texts:

        return []

    embedding_model = get_model()

    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )

    k = min(3, len(texts))

    distances, indices = index.search(
        query_embedding,
        k
    )

    results = []

    for idx in indices[0]:

        if idx < 0 or idx >= len(texts):
            continue

        results.append(texts[idx])

    return results


def refresh_index():

    global index
    global texts

    index = None
    texts = []

    index, texts = build_index()
