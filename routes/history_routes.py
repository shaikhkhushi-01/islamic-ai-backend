from fastapi import APIRouter, Depends

from auth import get_current_user
from services.history_service import (
    get_history,
    clear_history
)

router = APIRouter()


@router.get("/history")
def history(
    current_user=Depends(get_current_user)
):

    rows = get_history(current_user["id"])

    return {
        "history": [
            {
                "question": r[0],
                "answer": r[1]
            }
            for r in rows
        ]
    }


@router.delete("/clear")
def clear(
    current_user=Depends(get_current_user)
):

    clear_history(current_user["id"])

    return {
        "message": "Chat cleared successfully"
    }
