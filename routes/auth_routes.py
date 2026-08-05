from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
import sqlite3

from database import DB_PATH, hash_password, verify_password
from auth import create_access_token
from models.schemas import RegisterUser

router = APIRouter()


@router.post("/register")
def register(user: RegisterUser):

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
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_pw = hash_password(user.password)

    cursor.execute(
        """
        INSERT INTO users(username,email,password)
        VALUES(?,?,?)
        """,
        (
            username,
            email,
            hashed_pw
        )
    )

    conn.commit()
    conn.close()

    return {
        "message": "User registered successfully"
    }


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = form_data.username.lower().strip()

    cursor.execute(
        """
        SELECT id,password
        FROM users
        WHERE email=?
        """,
        (email,)
    )

    row = cursor.fetchone()

    conn.close()

    if not row:
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials"
        )

    user_id, hashed_password = row

    if not verify_password(
        form_data.password,
        hashed_password
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials"
        )

    token = create_access_token(
        {
            "sub": str(user_id)
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }
