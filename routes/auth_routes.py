from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

from models.schemas import RegisterUser
from services.auth_service import register_user, login_user

router = APIRouter()


@router.post("/register")
def register(user: RegisterUser):

    success = register_user(user)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    return {
        "message": "User registered successfully"
    }


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    token = login_user(
        form_data.username,
        form_data.password
    )

    if token is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials"
        )

    return {
        "access_token": token,
        "token_type": "bearer"
    }
