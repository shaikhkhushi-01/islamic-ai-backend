import sqlite3

from database import DB_PATH, hash_password


def seed_data():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    data = [

        # -------- BASIC KNOWLEDGE --------

        (
            "prayer",
            "🕌 Salah is one of the Five Pillars of Islam.",
            "knowledge",
            """🕌 WHY WE PRAY (SALAH)

Salah is a direct connection between a servant and Allah.

📖 Quran (29:45):
"Indeed, prayer prevents immorality and wrongdoing."

The Prophet ﷺ said:
"The first matter that the slave will be brought to account for on the Day of Judgment is the prayer."

✨ Practical Advice:
Pray slowly, understand meanings, and treat it like a meeting with Allah.

🤲 Remember:
Prayer is not a burden — it is spiritual oxygen.
"""
        ),

        ("zakat", "💰 Zakat is 2.5% of yearly savings given to the needy.", "knowledge"),
        ("fasting", "🌙 Fasting in Ramadan teaches patience and self-control.", "knowledge"),
        ("hajj", "🕋 Hajj is pilgrimage to Makkah, required once if financially able.", "knowledge"),
        ("quran", "📖 Quran is the holy book revealed to Prophet Muhammad ﷺ.", "knowledge"),
        ("prophet", "🌟 Prophet Muhammad ﷺ is the final messenger of Islam.", "knowledge"),
        ("iman", "✨ Iman means faith in Allah, angels, books, messengers, day of judgment, destiny.", "knowledge"),
        ("islam", "☪ Islam means submission to the will of Allah.", "knowledge"),
        ("ihsan", "🌸 Ihsan means worship Allah as if you see Him.", "knowledge"),
        ("ramadan", "🌙 Ramadan is the 9th month of Islamic calendar.", "knowledge"),
        ("eid", "🎉 Eid is a festival celebrated after Ramadan and Hajj.", "knowledge"),
        ("charity", "🤝 Charity increases blessings and removes sins.", "knowledge"),
        ("dua", "🙏 Dua is supplication made to Allah.", "knowledge"),
        ("tawheed", "🕊 Tawheed means belief in oneness of Allah.", "knowledge"),
        ("angels", "👼 Angels are created from light.", "knowledge"),
        ("jannah", "🌿 Jannah is paradise promised to believers.", "knowledge"),
        ("jahannam", "🔥 Jahannam is hellfire.", "knowledge"),
        ("wudu", "💧 Wudu is purification before prayer.", "knowledge"),
        ("ghusl", "🚿 Ghusl is full body purification.", "knowledge"),
        ("adhan", "📢 Adhan is call to prayer.", "knowledge"),
        ("sunnah", "📜 Sunnah are teachings of Prophet ﷺ.", "knowledge"),
        ("hadith", "📚 Hadith are sayings of Prophet Muhammad ﷺ.", "knowledge"),
        ("umrah", "🕋 Umrah is minor pilgrimage.", "knowledge"),
        ("sawm", "🌙 Sawm means fasting.", "knowledge"),
        ("salah", "🕌 Salah means prayer.", "knowledge"),
        ("shahada", "☝ Shahada is declaration of faith.", "knowledge"),
        ("hijab", "🧕 Hijab is modest dress in Islam.", "knowledge"),
        ("halal", "✅ Halal means permissible.", "knowledge"),
        ("haram", "❌ Haram means forbidden.", "knowledge"),
        ("qiyamah", "⏳ Qiyamah is the Day of Judgment.", "knowledge"),

        # -------- LIFE GUIDANCE --------

        (
            "music",
            "🎵 Some scholars consider music haram, others allow soft nasheeds without instruments. Avoid anything that leads to sin.",
            "guidance"
        ),

        (
            "stress",
            "🧠 When stressed, remember Allah, pray 2 rakah, and make dua. Allah says 'Verily in remembrance of Allah do hearts find rest.'",
            "guidance"
        ),

        (
            "depression",
            "💙 Islam encourages seeking help and making dua.",
            "guidance",
            """💙 FEELING DEPRESSED IN ISLAM

Islam acknowledges emotional pain.

📖 Quran (94:5-6):
"Indeed, with hardship comes ease."

Even Prophet Muhammad ﷺ faced sadness (Year of Sorrow).

✨ Practical Steps:
• Pray 2 rakah
• Make dua
• Talk to someone trusted
• Seek professional help if needed

🤲 Allah tests those He loves. Your pain is not ignored.
"""
        ),

        (
            "travel prayer",
            "✈️ While travelling, you can shorten 4 rakah prayers to 2 rakah (Qasr).",
            "guidance"
        ),

        (
            "forgiveness",
            "🤲 Allah is Most Forgiving. Sincerely repent and avoid repeating the sin.",
            "guidance"
        ),

        (
            "patience",
            "⏳ Allah loves those who are patient (Sabr). Hardships remove sins.",
            "guidance"
        ),

        (
            "gratitude",
            "🌼 If you are grateful, Allah will increase you (Quran 14:7).",
            "guidance"
        ),

        (
            "halal income",
            "💼 Earning halal sustains blessings in life. Avoid interest (riba) and fraud.",
            "guidance"
        ),

        (
            "parents",
            "👨‍👩‍👧 Islam commands kindness to parents after worship of Allah.",
            "guidance"
        ),

        (
            "anger",
            "🔥 Control anger. Prophet ﷺ said: The strong person is the one who controls himself when angry.",
            "guidance"
        ),
    ]

    # =========================================================
    # INSERT KNOWLEDGE
    # =========================================================

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
                (
                    topic,
                    content,
                    type,
                    detailed_content
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    topic,
                    content,
                    type_,
                    detailed
                )
            )

    # =========================================================
    # CREATE / UPDATE DEFAULT ADMIN
    # =========================================================

    admin_email = "admin@gmail.com"
    admin_username = "admin"
    admin_password = "12345678"

    hashed_password = hash_password(admin_password)

    cursor.execute(
        "SELECT id FROM users WHERE email=?",
        (admin_email,)
    )

    existing_admin = cursor.fetchone()

    if existing_admin:

        cursor.execute(
            """
            UPDATE users
            SET
                username = ?,
                password = ?,
                role = ?
            WHERE email = ?
            """,
            (
                admin_username,
                hashed_password,
                "admin",
                admin_email
            )
        )

    else:

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password,
                role
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                admin_username,
                admin_email,
                hashed_password,
                "admin"
            )
        )

    # =========================================================
    # SAVE
    # =========================================================

    conn.commit()
    conn.close()
