import sqlite3

from database import DB_PATH, hash_password, verify_password
from auth import create_access_token


def register_user(user):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = user.email.lower().strip()
    username = user.username.strip()

    cursor.execute(
        "SELECT id FROM users WHERE email=?",
        (email,)
    )

    if cursor.fetchone():
        conn.close()
        return None

    hashed = hash_password(user.password)

    cursor.execute(
        """
        INSERT INTO users(username,email,password)
        VALUES(?,?,?)
        """,
        (
            username,
            email,
            hashed
        )
    )

    conn.commit()
    conn.close()

    return True


def login_user(email, password):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id,password
        FROM users
        WHERE email=?
        """,
        (
            email.lower().strip(),
        )
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    user_id, hashed = row

    if not verify_password(password, hashed):
        return None

    token = create_access_token(
        {"sub": str(user_id)}
    )

    return token
