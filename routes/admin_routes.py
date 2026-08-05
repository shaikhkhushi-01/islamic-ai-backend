import sqlite3

from fastapi import (
    APIRouter,
    Depends,
    Form,
    File,
    UploadFile
)

from pypdf import PdfReader

from database import DB_PATH
from auth import require_admin

from rag_engine import refresh_index

router = APIRouter()


@router.post("/admin/add")
def add_topic(

    current_user: dict = Depends(require_admin),

    topic: str = Form(...),

    content: str = Form(...),

    detailed: str = Form(""),

    reference: str = Form("")

):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO knowledge
        (
            topic,
            content,
            type,
            detailed_content,
            reference
        )
        VALUES(?,?,?,?,?)
        """,
        (
            topic,
            content,
            "general",
            detailed,
            reference
        )
    )

    conn.commit()

    conn.close()

    refresh_index()

    return {

        "message": "Topic added successfully"

    }


@router.post("/admin/upload-pdf")
def upload_pdf(

    file: UploadFile = File(...),

    current_user: dict = Depends(require_admin)

):

    text = ""

    pdf = PdfReader(file.file)

    for page in pdf.pages:

        extracted = page.extract_text()

        if extracted:

            text += extracted + "\n"

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO knowledge
        (
            topic,
            content,
            type,
            detailed_content,
            reference
        )
        VALUES(?,?,?,?,?)
        """,
        (
            file.filename,
            text[:500],
            "book",
            text,
            file.filename
        )
    )

    conn.commit()

    conn.close()

    refresh_index()

    return {

        "message": "PDF uploaded successfully"

    }
