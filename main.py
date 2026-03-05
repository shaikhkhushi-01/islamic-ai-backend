from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import sqlite3

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")
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