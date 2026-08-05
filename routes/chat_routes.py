from fastapi import APIRouter, Depends

from auth import get_current_user
from models.schemas import Message
from ai_engine import handle_greeting
from services.chat_service import process_chat

router = APIRouter()


@router.post("/chat")
def chat(
    data: Message,
    current_user: dict = Depends(get_current_user)
):

    user_msg = data.message.strip()

    if not user_msg:

        return {
            "reply": "Please ask something meaningful."
        }

    greeting = handle_greeting(user_msg)

    if greeting:

        return {

            "reply": greeting,

            "related_topics": []

        }

    return process_chat(
        user_msg,
        current_user
    )
