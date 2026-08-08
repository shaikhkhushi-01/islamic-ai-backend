import re
from groq import Groq
from config import GROQ_API_KEY

groq_client = Groq(api_key=GROQ_API_KEY)


# ================= EMOTION =================

def detect_emotion(user_msg):

    user_msg = user_msg.lower()

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


# ================= INTENT =================

def detect_intent(text):

    text = text.lower()

    if re.search(r"\bi feel\b|\bstressed\b|\bsad\b|\bdepressed\b|\bdua\b", text):
        return "spiritual"

    if re.search(r"\bis .* haram\b|\bis .* halal\b|\bcan i\b|\ballowed\b", text):
        return "ruling"

    if re.search(r"\bwhat is\b|\bmeaning\b|\bexplain\b|\btell me about\b", text):
        return "knowledge"

    return "knowledge"


# ================= GREETINGS =================

def handle_greeting(message):

    msg = message.lower()

    greetings = [
        "hi",
        "hello",
        "assalamualaikum",
        "salam",
        "hey"
    ]

    if msg in greetings:
        return (
            "Assalamu Alaikum 😊\n\n"
            "Welcome to Islamic AI.\n"
            "You can ask me about:\n\n"
            "📖 Quran\n"
            "📚 Hadith\n"
            "🤲 Dua\n"
            "🕌 Salah\n"
            "🌙 Ramadan\n"
            "💚 Islamic Guidance"
        )

    return None


# ================= GROQ =================
# ================= GROQ =================

def ask_groq(prompt):

    response = groq_client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content
