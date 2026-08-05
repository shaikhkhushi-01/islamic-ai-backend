from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from services.seed_service import seed_data

from routes.chat_routes import router as chat_router
from routes.auth_routes import router as auth_router
from routes.admin_routes import router as admin_router
from routes.history_routes import router as history_router


app = FastAPI(
    title="Islamic AI API",
    version="2.0.0",
    description="MBZUAI Level Islamic AI Assistant"
)


# =========================
# CORS
# =========================

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


# =========================
# Routers
# =========================

app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(history_router)


# =========================
# Startup
# =========================

@app.on_event("startup")
def startup():

    init_db()

    seed_data()


# =========================
# Root
# =========================

@app.get("/")
def home():

    return {
        "status": "running",
        "project": "Islamic AI Assistant",
        "version": "2.0"
    }
