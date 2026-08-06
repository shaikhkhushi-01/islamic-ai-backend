from fastapi import APIRouter, Depends, Form

from auth import require_admin
from services.admin_service import add_topic

router = APIRouter()


@router.post("/admin/add")
def admin_add(

    topic: str = Form(...),

    content: str = Form(...),

    detailed: str = Form(""),

    reference: str = Form(""),

    current_user=Depends(require_admin)

):

    add_topic(
        topic,
        content,
        detailed,
        reference
    )

    return {
        "message": "Topic added successfully"
    }
