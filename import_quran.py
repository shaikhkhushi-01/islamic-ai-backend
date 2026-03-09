import json
import sqlite3

DB_PATH = "islamic_ai.db"

with open("quran_json.json", "r", encoding="utf-8") as f:
    data = json.load(f)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create table
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

# Clear old data (important)
cursor.execute("DELETE FROM quran")

count = 0

for surah in data:

    surah_no = surah["id"]

    for verse in surah["verses"]:

        ayah_no = verse["id"]
        text = verse["text"]

        # Translation safe fallback
        translation = verse.get("translation", "")

        cursor.execute("""
        INSERT INTO quran (surah, ayah, text, translation, topic)
        VALUES (?, ?, ?, ?, ?)
        """, (
            surah_no,
            ayah_no,
            text,
            translation,
            ""
        ))

        count += 1

conn.commit()
conn.close()

print(f"✅ {count} Quran ayah imported successfully")
