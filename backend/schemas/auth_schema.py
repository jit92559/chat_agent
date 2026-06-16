from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class RegisterResponse(BaseModel):
    message: str
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class LoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str