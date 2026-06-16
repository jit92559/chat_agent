from fastapi import APIRouter

from schemas.auth_schema import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
)

from controllers.auth_controllers import (
    register_controller,
    login_controller,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"],
)


@router.post(
    "/register",
    response_model=RegisterResponse,
)
async def register(
    data: RegisterRequest,
):
    return await register_controller(data)


@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    data: LoginRequest,
):
    return await login_controller(data)