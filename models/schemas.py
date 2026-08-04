from pydantic import BaseModel


class Message(BaseModel):
    message: str


class RegisterUser(BaseModel):
    username: str
    email: str
    password: str


class LoginUser(BaseModel):
    email: str
    password: str
