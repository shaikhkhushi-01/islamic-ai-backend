import sqlite3
from database import DB_PATH


def seed_data():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    data = [

        # -------- BASIC KNOWLEDGE --------

        # 👇 YAHAN APNA POORA data = [...] WALA LIST
        # main.py se COPY karke paste kar do.
        # ("prayer", ...)
        # ("zakat", ...)
        # ("fasting", ...)
        # ...
        # ("anger", ...)

    ]

    for item in data:

        if len(item) == 4:
            topic, content, type_, detailed = item
        else:
            topic, content, type_ = item
            detailed = None

        cursor.execute(
            "SELECT id FROM knowledge WHERE topic=?",
            (topic,)
        )

        if not cursor.fetchone():

            cursor.execute(
                """
                INSERT INTO knowledge
                (topic, content, type, detailed_content)
                VALUES (?, ?, ?, ?)
                """,
                (
                    topic,
                    content,
                    type_,
                    detailed
                )
            )

    conn.commit()
    conn.close()
