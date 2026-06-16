from fastapi import FastAPI
from routers.user_routers import router as user_router
from routers.test_uload_router import router as test_upload_router

from routers.auth_routers import router as auth_router
# from backend.routers.protected_router import router as protected_router
from middlewares.auth_middlewares import AuthMiddleware
app = FastAPI(
    title="Chatbot API",
    version="1.0.0"
)
app.add_middleware(AuthMiddleware)

app.include_router(auth_router)
# app.include_router(protected_router)
app.include_router(user_router)
app.include_router(test_upload_router)
@app.get("/")
async def root():
    return {
        "message": "Chatbot Backend Running"
    }



