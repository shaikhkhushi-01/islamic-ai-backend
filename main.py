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
from datetime import datetime
import re
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set in environment")
                      
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

    conn.commit()
    conn.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

ADMIN_PASSWORD = "admin123"
# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("islamic_ai.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS islamic_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        category TEXT,
        madhab TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- DATABASE FUNCTIONS ----------------

def get_all_data():
    conn = sqlite3.connect("islamic_ai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM islamic_data ORDER BY id DESC")
    data = cursor.fetchall()
    conn.close()
    return data

def add_data(text, category, madhab):
    conn = sqlite3.connect("islamic_ai.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO islamic_data (text, category, madhab) VALUES (?, ?, ?)",
        (text, category, madhab if madhab else None)
    )
    conn.commit()
    conn.close()

def delete_data(item_id):
    conn = sqlite3.connect("islamic_ai.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM islamic_data WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def update_data(item_id, text, category, madhab):
    conn = sqlite3.connect("islamic_ai.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE islamic_data
        SET text = ?, category = ?, madhab = ?
        WHERE id = ?
    """, (text, category, madhab if madhab else None, item_id))
    conn.commit()
    conn.close()

# ---------------- SEARCH ----------------

def search_database(query, selected_madhab=None):
    conn = sqlite3.connect("islamic_ai.db")
    cursor = conn.cursor()

    query_like = f"%{query}%"

    if selected_madhab:
        cursor.execute("""
            SELECT text FROM islamic_data
            WHERE text LIKE ? AND (madhab = ? OR madhab IS NULL)
        """, (query_like, selected_madhab))
    else:
        cursor.execute("SELECT text FROM islamic_data WHERE text LIKE ?", (query_like,))

    results = cursor.fetchall()
    conn.close()
    return [r[0] for r in results[:5]]

# ---------------- HOME ----------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    request.session["chat"] = []
    return render_chat([])

@app.post("/chat", response_class=HTMLResponse)
def chat(request: Request, query: str = Form(...), madhab: str = Form(None)):
    chat_history = request.session.get("chat", [])
    results = search_database(query, madhab)

    response_text = "<br><br>".join(results) if results else "❌ No relevant results found."

    chat_history.append({"user": query, "bot": response_text})
    request.session["chat"] = chat_history

    return render_chat(chat_history)

# ---------------- ADMIN LOGIN ----------------

@app.get("/admin", response_class=HTMLResponse)
def admin_login(request: Request):
    if request.session.get("admin_logged_in"):
        return RedirectResponse("/admin/panel", status_code=302)

    return """
    <h2>🔐 Admin Login</h2>
    <form method="post">
        <input type="password" name="password" required>
        <button type="submit">Login</button>
    </form>
    """

@app.post("/admin", response_class=HTMLResponse)
def admin_auth(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["admin_logged_in"] = True
        return RedirectResponse("/admin/panel", status_code=302)
    return "<h3>❌ Wrong Password</h3><a href='/admin'>Try Again</a>"

# ---------------- ADMIN PANEL ----------------

@app.get("/admin/panel", response_class=HTMLResponse)
def admin_panel(request: Request):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin", status_code=302)

    data = get_all_data()

    rows = ""
    for item in data:
        rows += f"""
        <tr>
            <td>{item[0]}</td>
            <td>{item[2]}</td>
            <td>{item[3]}</td>
            <td>{item[1]}</td>
            <td>
                <a href="/admin/edit/{item[0]}">Edit</a> |
                <a href="/admin/delete/{item[0]}">Delete</a>
            </td>
        </tr>
        """

    return f"""
    <h2>Admin Panel</h2>
    <a href="/admin/add">➕ Add New</a><br><br>
    <table border="1" cellpadding="5">
        <tr>
            <th>ID</th>
            <th>Category</th>
            <th>Madhab</th>
            <th>Text</th>
            <th>Action</th>
        </tr>
        {rows}
    </table>
    <br><a href="/">Go to Chat</a>
    """

# ---------------- ADD ----------------

@app.get("/admin/add", response_class=HTMLResponse)
def add_page(request: Request):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin", status_code=302)

    return """
    <h2>Add Data</h2>
    <form method="post">
        <textarea name="text" required></textarea><br>
        <input name="category" placeholder="Category"><br>
        <input name="madhab" placeholder="Madhab"><br>
        <button type="submit">Save</button>
    </form>
    """

@app.post("/admin/add")
def add_submit(request: Request, text: str = Form(...), category: str = Form(...), madhab: str = Form(None)):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin", status_code=302)

    add_data(text, category, madhab)
    return RedirectResponse("/admin/panel", status_code=302)

# ---------------- DELETE ----------------

@app.get("/admin/delete/{item_id}")
def delete_item(request: Request, item_id: int):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin", status_code=302)

    delete_data(item_id)
    return RedirectResponse("/admin/panel", status_code=302)

# ---------------- EDIT ----------------

@app.get("/admin/edit/{item_id}", response_class=HTMLResponse)
def edit_page(request: Request, item_id: int):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin", status_code=302)

    conn = sqlite3.connect("islamic_ai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM islamic_data WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()

    return f"""
    <h2>Edit Data</h2>
    <form method="post">
        <textarea name="text">{item[1]}</textarea><br>
        <input name="category" value="{item[2]}"><br>
        <input name="madhab" value="{item[3] if item[3] else ''}"><br>
        <button type="submit">Update</button>
    </form>
    """

@app.post("/admin/edit/{item_id}")
def edit_submit(request: Request, item_id: int, text: str = Form(...), category: str = Form(...), madhab: str = Form(None)):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin", status_code=302)

    update_data(item_id, text, category, madhab)
    return RedirectResponse("/admin/panel", status_code=302)

# ---------------- CHAT UI ----------------

def render_chat(chat_history):
    messages_html = ""
    for chat in chat_history:
        messages_html += f"""
        <div class="user-msg">
            <div class="bubble user-bubble">
                {chat['user']}
            </div>
        </div>

        <div class="bot-msg">
            <div class="bubble bot-bubble">
                {chat['bot']}
            </div>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Islamic AI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(to right, #1e3c72, #2a5298);
                display: flex;
                justify-content: center;
                padding: 20px;
            }}

            .chat-container {{
                width: 100%;
                max-width: 700px;
                background: white;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                display: flex;
                flex-direction: column;
                height: 90vh;
            }}

            .chat-header {{
                text-align: center;
                font-size: 22px;
                font-weight: bold;
                margin-bottom: 15px;
                color: #2a5298;
            }}

            .chat-box {{
                flex: 1;
                overflow-y: auto;
                padding-right: 10px;
            }}

            .user-msg {{
                display: flex;
                justify-content: flex-end;
                margin: 10px 0;
            }}

            .bot-msg {{
                display: flex;
                justify-content: flex-start;
                margin: 10px 0;
            }}

            .bubble {{
                padding: 12px 15px;
                border-radius: 20px;
                max-width: 75%;
                font-size: 14px;
                line-height: 1.5;
            }}

            .user-bubble {{
                background: #2a5298;
                color: white;
                border-bottom-right-radius: 5px;
            }}

            .bot-bubble {{
                background: #f1f1f1;
                color: black;
                border-bottom-left-radius: 5px;
            }}

            .input-area {{
                display: flex;
                margin-top: 10px;
                gap: 10px;
            }}

            input {{
                flex: 1;
                padding: 12px;
                border-radius: 25px;
                border: 1px solid #ccc;
                outline: none;
            }}

            button {{
                padding: 12px 18px;
                border-radius: 25px;
                border: none;
                background: #2a5298;
                color: white;
                cursor: pointer;
                font-weight: bold;
            }}

            button:hover {{
                background: #1e3c72;
            }}

            .admin-link {{
                text-align: center;
                margin-top: 10px;
                font-size: 12px;
            }}

            .admin-link a {{
                text-decoration: none;
                color: #2a5298;
            }}

        </style>
    </head>

    <body>
        <div class="chat-container">
            <div class="chat-header">🕌 Islamic AI Assistant</div>

            <div class="chat-box">
                {messages_html}
            </div>

            <form action="/chat" method="post">
                <div class="input-area">
                    <input type="text" name="query" placeholder="Ask your question..." required>
                    <input type="text" name="madhab" placeholder="Madhab (optional)">
                    <button type="submit">Send</button>
                </div>
            </form>

            <div class="admin-link">
                <a href="/admin">Admin Login</a>
            </div>
        </div>
    </body>
    </html>
    """
# ================= MODEL =================

class Message(BaseModel):
    message: str

def seed_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    data = [

        # -------- BASIC KNOWLEDGE --------
        ("prayer",
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
        ("music", "🎵 Some scholars consider music haram, others allow soft nasheeds without instruments. Avoid anything that leads to sin.", "guidance"),
        ("stress", "🧠 When stressed, remember Allah, pray 2 rakah, and make dua. Allah says 'Verily in remembrance of Allah do hearts find rest.'", "guidance"),
        ("depression",
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
        ("travel prayer", "✈️ While travelling, you can shorten 4 rakah prayers to 2 rakah (Qasr).", "guidance"),
        ("forgiveness", "🤲 Allah is Most Forgiving. Sincerely repent and avoid repeating the sin.", "guidance"),
        ("patience", "⏳ Allah loves those who are patient (Sabr). Hardships remove sins.", "guidance"),
        ("gratitude", "🌼 If you are grateful, Allah will increase you (Quran 14:7).", "guidance"),
        ("halal income", "💼 Earning halal sustains blessings in life. Avoid interest (riba) and fraud.", "guidance"),
        ("parents", "👨‍👩‍👧 Islam commands kindness to parents after worship of Allah.", "guidance"),
        ("anger", "🔥 Control anger. Prophet ﷺ said: The strong person is the one who controls himself when angry.", "guidance"),
    ]

    for item in data:
        if len(item) == 4:
            topic, content, type_, detailed_content = item
        else:
            topic, content, type_ = item
            detailed_content = None

        cursor.execute("SELECT * FROM knowledge WHERE topic=?", (topic,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO knowledge (topic, content, type, detailed_content) VALUES (?, ?, ?, ?)",
                (topic, content, type_, detailed_content)
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

    # ✅ Memory fallback
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

    conn.close()
    return None

def hash_password(password: str):
    return pwd_context.hash(password)

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

# ================= ROUTES =================

@app.get("/")
def home():
    return {"message": "Islamic AI Startup Backend Running"}

@app.post("/chat/")
def chat(data: Message, current_user: dict = Depends(get_current_user)):

    user_msg = data.message.strip()

    if not user_msg:
        return {"reply": "Please ask something meaningful."}

    session_id = str(current_user["id"])
    result = search_database(user_msg, session_id)

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

    return {
        "reply": reply,
        "related_topics": related
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