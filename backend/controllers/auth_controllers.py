from fastapi import HTTPException, status

from schemas.auth_schema import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
)

from services.auth_service import (
    register_user,
    authenticate_user,
    create_access_token,
)


async def register_controller(
    data: RegisterRequest,
) -> RegisterResponse:

    user = await register_user(
        name=data.name,
        email=data.email,
        password=data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    access_token = create_access_token(
        {
            "sub": user["email"],
            "user_id": user["_id"],
        }
    )

    return RegisterResponse(
        message="User registered successfully",
        access_token=access_token,
        token_type="bearer",
    )


async def login_controller(
    data: LoginRequest,
) -> LoginResponse:

    user = await authenticate_user(
        email=data.email,
        password=data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        {
            "sub": user["email"],
            "user_id": user["_id"],
        }
    )

    return LoginResponse(
        message="Login successful",
        access_token=access_token,
        token_type="bearer",
    )