import json
import sqlite3

DB_PATH = "islamic_ai.db"

with open("quran_json.json", "r", encoding="utf-8") as f:
    data = json.load(f)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS quran (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    surah INTEGER,
    ayah INTEGER,
    text TEXT,
    translation TEXT,
    topic TEXT
)
""")

for surah in data:

    surah_no = surah["id"]

    for verse in surah["verses"]:

        ayah_no = verse["id"]
        text = verse["text"]

        cursor.execute(
        "INSERT INTO quran (surah, ayah, text, translation, topic) VALUES (?,?,?,?,?)",
        (surah_no, ayah_no, text, verse.get("translation",""), "")
        )

conn.commit()
conn.close()

print("✅ 6236 Quran ayah imported successfully")
