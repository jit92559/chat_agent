from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import jwt, JWTError

from configs.auth_config import SECRET_KEY, ALGORITHM


PUBLIC_PATHS = [
    "/",
    "/docs",
    "/openapi.json",
    "/api/auth/register",
    "/api/auth/login",
    "/files/upload-rag"
]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in PUBLIC_PATHS:
            return await call_next(request)
        print(request.headers)
        auth_header = request.headers.get("Authorization")
        print(auth_header)
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "message": "Login required",
                    "redirect": "/login",
                },
            )

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
            )

            request.state.user = payload

        except JWTError:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "message": "Invalid or expired token",
                    "redirect": "/login",
                },
            )

        return await call_next(request)