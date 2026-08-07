from sentence_transformers import SentenceTransformer
from database import DB_PATH
import faiss
import numpy as np
import sqlite3

model = SentenceTransformer("all-MiniLM-L6-v2")


def build_index():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT topic, detailed_content, content
        FROM knowledge
    """)

    rows = cursor.fetchall()
    conn.close()

    texts = []
    metadata = []

    CHUNK_SIZE = 500

    for topic, detailed, content in rows:

        text = detailed if detailed else content

        if not text:
            continue

        for i in range(0, len(text), CHUNK_SIZE):

            chunk = text[i:i + CHUNK_SIZE]

            texts.append(chunk)

            metadata.append({
                "topic": topic,
                "chunk": chunk
            })

    embeddings = model.encode(texts)

    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype("float32"))

    return index, texts, metadata


index, texts, metadata = build_index()


def semantic_search(query):

    q = model.encode([query])

    D, I = index.search(
        np.array(q).astype("float32"),
        3
    )

    results = []

    for idx in I[0]:

        results.append({
            "topic": metadata[idx]["topic"],
            "text": texts[idx]
        })

    return results


def refresh_index():

    global index, texts, metadata

    index, texts, metadata = build_index()
