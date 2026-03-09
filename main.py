from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from difflib import get_close_matches
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
import re

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ================= DB PATH =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "islamic_ai.db")

print("DB PATH:", DB_PATH)

# ================= INIT DB =================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            content TEXT,
            type TEXT,
            detailed_content TEXT,
            reference TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT,
            answer TEXT,
            intent TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            last_topic TEXT
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user'
    )
""")

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
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hadith (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book TEXT,
        number INTEGER,
        text TEXT,
        topic TEXT
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tafsir (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        surah INTEGER,
        ayah INTEGER,
        explanation TEXT
    )
""")



    conn.commit()
    conn.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://islamic-ai-frontend.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= MODEL =================

class Message(BaseModel):
    message: str

def seed_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

def clean_text(text):

    text = text.lower()

    remove = ["why","what","is","the","tell","me","about","do","muslims"]

    for r in remove:
        text = text.replace(r,"")

    return text.strip()
def search_quran(user_msg):

    print("🔍 SEARCH_QURAN CALLED:", user_msg)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    words = user_msg.lower().split()

    cursor.execute(
        "SELECT surah, ayah, text, translation, topic FROM quran"
    )

    rows = cursor.fetchall()

    best_match = None
    best_score = 0

    for surah, ayah, text, translation, topic in rows:

        searchable = f"{text or ''} {translation or ''} {topic or ''}".lower()

        score = sum(word in searchable for word in words)

        if score > best_score:
            best_score = score
            best_match = (surah, ayah, text, translation)

    conn.close()

    if best_match and best_score > 0:

        surah, ayah, text, translation = best_match

        tafsir = search_tafsir(surah, ayah)

        result = f"""
📖 Quran {surah}:{ayah}

{text}

Meaning:
{translation}
"""

        if tafsir:
            result += f"\n\n📖 Tafsir:\n{tafsir}"

        return result

    return None
def seed_hadith():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    hadith_data = [

        ("Bukhari",1,
        "Actions are judged by intentions",
        "intention"),

        ("Muslim",32,
        "Allah does not look at your appearance but at your hearts",
        "heart"),

        ("Bukhari",6114,
        "The strong person is the one who controls anger",
        "anger")

    ]

    for book, number, text, topic in hadith_data:

        cursor.execute(
        "SELECT id FROM hadith WHERE book=? AND number=?",
        (book,number)
        )

        if not cursor.fetchone():

            cursor.execute(
            "INSERT INTO hadith (book, number, text, topic) VALUES (?,?,?,?)",
            (book,number,text,topic)
            )

    conn.commit()
    conn.close()

# ================= INTENT DETECTION =================

def detect_intent(text):

    text = text.lower()

    if re.search(r"\bi feel\b|\bstressed\b|\bsad\b|\bdepressed\b|\bdua\b", text):
        return "spiritual"

    if re.search(r"\bis .* haram\b|\bis .* halal\b|\bcan i\b|\ballowed\b", text):
        return "ruling"

    if re.search(r"\bwhat is\b|\bexplain\b|\btell me about\b|\bmeaning of\b", text):
        return "knowledge"

    return "knowledge"

# ================= MEMORY =================

def save_memory(session_id, topic):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_memory WHERE session_id=?", (session_id,))
    cursor.execute(
        "INSERT INTO chat_memory (session_id, last_topic) VALUES (?, ?)",
        (session_id, topic)
    )

    conn.commit()
    conn.close()


def get_memory(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT last_topic FROM chat_memory WHERE session_id=?", (session_id,))
    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None

def get_related_topics(current_topic):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT topic, type FROM knowledge")
    rows = cursor.fetchall()
    conn.close()

    # Current topic ka type nikaalo
    current_type = None
    for topic, type_ in rows:
        if topic == current_topic:
            current_type = type_
            break

    if not current_type:
        return []

    # Same type ke topics filter karo
    same_type_topics = [
        topic for topic, type_ in rows
        if type_ == current_type and topic != current_topic
    ]

    # Fuzzy similarity sort
    similar = get_close_matches(current_topic, same_type_topics, n=5, cutoff=0.3)

    return similar[:4]

# ================= SEARCH =================
def find_best_match(user_msg, topics):

    user_msg = user_msg.lower()

    # 1️⃣ Sort topics by length (longest first)
    topics_sorted = sorted(topics, key=len, reverse=True)

    # 2️⃣ Exact topic match (longer first)
    for topic in topics_sorted:
        if topic.lower() in user_msg:
            return topic

    # 3️⃣ Word match
    words = user_msg.split()
    for word in words:
        if word in topics:
            return word

    # 4️⃣ Fuzzy match
    for word in words:
        match = get_close_matches(word, topics, n=1, cutoff=0.75)
        if match:
            return match[0]

    return None

def search_database(user_msg, session_id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    user_msg = user_msg.lower()

    synonyms = {
        "sad": "depression",
        "depressed": "depression",
        "tension": "stress",
        "worried": "stress",
        "traveling": "travel prayer",
        "journey": "travel prayer",
        "song": "music",
        "songs": "music",
        "pray": "prayer",
        "praying": "prayer",
        "namaz": "prayer",
    }

    for word, replacement in synonyms.items():
        if word in user_msg:
            user_msg = user_msg.replace(word, replacement)

    cursor.execute("SELECT topic, content, detailed_content, reference FROM knowledge")
    rows = cursor.fetchall()

    topics = [row[0] for row in rows]

    # ✅ Direct keyword priority
    if "music" in user_msg:
        best_topic = "music"
    elif "haram" in user_msg and "music" not in user_msg:
        best_topic = "haram"
    else:
        best_topic = find_best_match(user_msg, topics)

    # ✅ Common handling for ALL cases
    if best_topic:
        for topic, content, detailed, reference in rows:
            if topic == best_topic:
                save_memory(session_id, topic)

                reply_text = detailed if detailed else content

                if reference:
                 reply_text += f"\n\n📖 Reference: {reference}"

                # ✅ EMOTION ADD START
                emotion = detect_emotion(user_msg)

                if emotion == "sad":
                    reply_text += "\n\n🤲 Dua: Allahumma inni a'udhu bika minal-hammi wal-hazan."
                elif emotion == "anxiety":
                    reply_text += "\n\n📿 Zikr: Hasbunallahu wa ni'mal wakeel."
                elif emotion == "guilt":
                    reply_text += "\n\n🕊 Tawbah: Say 'Astaghfirullah' sincerely."
                elif emotion == "anger":
                    reply_text += "\n\n📜 Hadith: The strong person controls anger."
                # ✅ EMOTION ADD END

                related = get_related_topics(topic)

                conn.close()

                return {
                    "text": reply_text,
                    "related": related
                }

# Memory fallback
    last_topic = get_memory(session_id)

    if last_topic:
        cursor.execute(
            "SELECT content, detailed_content, reference FROM knowledge WHERE topic=?",
            (last_topic,)
        )
        row = cursor.fetchone()

        if row:
            content, detailed, reference = row
            conn.close()
            return {
                "text": detailed if detailed else content,
                "related": []
            }

    # Quran fallback search
    quran_result = search_quran(user_msg)

    if quran_result:
        conn.close()
        return {
            "text": quran_result,
            "related": []
        }

    conn.close()
    return None

def hash_password(password: str):
    try:
        return pwd_context.hash(password)
    except:
        return pwd_context.hash(password[:72])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

class RegisterUser(BaseModel):
    username: str
    email: str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str

def get_current_user(token: str = Depends(oauth2_scheme)):

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except JWTError:
        raise credentials_exception

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user is None:
        raise credentials_exception

    return {
        "id": user[0],
        "username": user[1],
        "role": user[2]
    }

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

from deep_translator import GoogleTranslator

def translate_text(text, target="en"):

    try:
        translated = GoogleTranslator(source='auto', target=target).translate(text)
        return translated
    except:
        return text
    
def search_tafsir(surah, ayah):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT explanation FROM tafsir WHERE surah=? AND ayah=?",
        (surah, ayah)
    )

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None

def clean_text(text):

    text = text.lower()

    remove = ["why", "what", "is", "the", "tell", "me", "about", "do", "muslims"]

    for r in remove:
        text = text.replace(r, "")

    return text.strip()
def search_hadith(user_msg):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    user_msg = user_msg.lower()

    cursor.execute("SELECT book, number, text, topic FROM hadith")

    rows = cursor.fetchall()

    for book, number, text, topic in rows:

        if topic in user_msg:

            conn.close()

            return f"""
📚 Hadith ({book} {number})

{text}
"""

    conn.close()
    return None
def seed_quran():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM quran LIMIT 1")

    if cursor.fetchone():
        conn.close()
        return

    sample = [
        (2,183,"O you who believe, fasting is prescribed for you","Fasting is obligatory","fasting"),
        (94,5,"Indeed with hardship comes ease","Allah promises ease after hardship","patience")
    ]

    for surah, ayah, text, translation, topic in sample:
        cursor.execute(
        "INSERT INTO quran (surah, ayah, text, translation, topic) VALUES (?,?,?,?,?)",
        (surah, ayah, text, translation, topic)
        )

    conn.commit()
    conn.close()
# ================= ROUTES =================

@app.get("/")
def home():
    return {"message": "Islamic AI Startup Backend Running"}

@app.post("/chat")
def chat(data: Message, current_user: dict = Depends(get_current_user)):

    user_msg = data.message.strip()
    user_msg = translate_text(user_msg, "en")

    if not user_msg:
        return {"reply": "Please ask something meaningful."}

    session_id = str(current_user["id"])

    # 🔎 Quran search FIRST
    quran_result = search_quran(user_msg)

    if quran_result:

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO chat_history (user_id, question, answer, intent, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (
            current_user["id"],
            user_msg,
            quran_result,
            "quran",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        return {
            "reply": quran_result,
            "related_topics": []
        }

    # 🧠 AI engine (existing system)
    result = islamic_ai_engine(user_msg, session_id)

    if not result:
        return {"reply": "🤖 I do not have detailed information yet."}

    reply = result["text"]
    related = result["related"]

    # Save history
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO chat_history (user_id, question, answer, intent, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        current_user["id"],
        user_msg,
        reply,
        "knowledge",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    reply = translate_text(reply, "en")

    return {
        "reply": reply,
        "related_topics": related
    }

def islamic_ai_engine(user_msg, session_id):

    # clean message
    user_msg = clean_text(user_msg)

    # 1️⃣ Quran search
    quran = search_quran(user_msg)

    if quran:
        return {
            "text": quran,
            "related": []
        }

    # 2️⃣ Hadith search
    hadith = search_hadith(user_msg)

    if hadith:
        return {
            "text": hadith,
            "related": []
        }

    # 3️⃣ Knowledge search
    knowledge = search_database(user_msg, session_id)

    if knowledge:
        return knowledge

    answer = ""

    if quran:
        answer += quran + "\n\n"

    if hadith:
        answer += hadith + "\n\n"

    if knowledge:
        answer += knowledge["text"]

    if answer.strip() == "":
        return None

    return {
        "text": answer,
        "related": knowledge["related"] if knowledge else []
    }

@app.get("/history")
def history(current_user: dict = Depends(get_current_user)):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT question, answer FROM chat_history WHERE user_id=? ORDER BY id ASC",
        (current_user["id"],)
    )

    rows = cursor.fetchall()
    conn.close()

    return {
        "history": [
            {"question": r[0], "answer": r[1]} for r in rows
        ]
    }

@app.delete("/clear")
def clear_chat(current_user: dict = Depends(get_current_user)):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM chat_history WHERE user_id=?", (current_user["id"],))

    conn.commit()
    conn.close()

    return {"message": "Chat cleared successfully"}

def detect_emotion(user_msg):

    emotions = {
        "sad": ["sad", "depressed", "lonely"],
        "anxiety": ["stress", "tension", "worried"],
        "guilt": ["sin", "haram", "gunah"],
        "anger": ["angry", "rage"]
    }

    for emotion, words in emotions.items():
        for word in words:
            if word in user_msg:
                return emotion

    return None

@app.post("/admin/add")
def add_topic(
    current_user: dict = Depends(require_admin),
    topic: str = Form(...),
    content: str = Form(...),
    detailed: str = Form(""),
    reference: str = Form("")
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO knowledge (topic, content, type, detailed_content, reference)
        VALUES (?, ?, ?, ?, ?)
    """, (topic, content, "general", detailed, reference))

    conn.commit()
    conn.close()

    return {"message": "Topic added successfully"}

@app.post("/register")
def register(user: RegisterUser):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = user.email.lower().strip()
    username = user.username.strip()

    cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)

    cursor.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, hashed_pw)
    )

    conn.commit()
    conn.close()

    return {"message": "User registered successfully"}

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = form_data.username.lower().strip()

    cursor.execute(
        "SELECT id, password FROM users WHERE email=?",
        (email,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    user_id, hashed_password = row

    if not verify_password(form_data.password, hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user_id)})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.on_event("startup")
def startup_event():
    init_db()
    seed_data()
    seed_quran()
    seed_hadith()

    # 🔥 AUTO CREATE ADMIN IF NOT EXISTS
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=?", ("admin@gmail.com",))

    if not cursor.fetchone():
        hashed_pw = hash_password("123456")
        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            ("admin", "admin@gmail.com", hashed_pw, "admin")
        )
        conn.commit()

    conn.close()
