from fastapi import APIRouter
from pydantic import BaseModel

from auth import get_current_user
from fastapi import Depends

from services.feedback_service import save_feedback

router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"]
)


class Feedback(BaseModel):

    question: str
    answer: str
    rating: str


@router.post("/")
def feedback(
    data: Feedback,
    current_user: dict = Depends(get_current_user)
):

    save_feedback(
        current_user["id"],
        data.question,
        data.answer,
        data.rating
    )

    return {
        "message": "Feedback saved successfully"
    }
