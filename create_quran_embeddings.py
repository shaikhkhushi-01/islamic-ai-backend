import sqlite3
import pickle
from sentence_transformers import SentenceTransformer

DB_PATH = "islamic_ai.db"

model = SentenceTransformer("all-MiniLM-L6-v2")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT surah, ayah, text, translation FROM quran")

rows = cursor.fetchall()

texts = []

for surah, ayah, text, translation in rows:
    texts.append(f"{text} {translation}")

embeddings = model.encode(texts)

data = {
    "rows": rows,
    "embeddings": embeddings
}

with open("quran_embeddings.pkl","wb") as f:
    pickle.dump(data,f)

print("✅ Quran embeddings created")