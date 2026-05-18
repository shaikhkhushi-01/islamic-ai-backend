from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import sqlite3

model = SentenceTransformer("all-MiniLM-L6-v2")

def build_index():
    conn = sqlite3.connect("islamic_ai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT topic, detailed_content, content FROM knowledge")
    rows = cursor.fetchall()
    conn.close()

    texts = []
    for row in rows:
        topic, detailed, content = row
        texts.append(detailed if detailed else content)

    embeddings = model.encode(texts)

    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype("float32"))

    return index, texts

index, texts = build_index()

def semantic_search(query):
    q = model.encode([query])
    D, I = index.search(np.array(q).astype("float32"), 3)

    results = []
    for idx in I[0]:
        results.append(texts[idx])

    return "\n\n".join(results)
def refresh_index():
    global index, texts
    index, texts = build_index()
