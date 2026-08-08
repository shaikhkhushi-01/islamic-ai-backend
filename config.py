import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not configured")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not configured")
