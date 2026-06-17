from fastapi import APIRouter, Request,Header
from schemas.auth_schema import UserResponse

router = APIRouter(
    prefix="/api/user",
    tags=["User"],
)


@router.get("/profile", response_model=UserResponse)
async def get_profile(request: Request):
    user = request.state.user

    return UserResponse(
        id=user["user_id"],
        name=user["name"],
        email=user["email"],
    )
