from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.user_routers import router as user_router
from routers.file_upload_router import router as test_upload_router
from routers.auth_routers import router as auth_router
# from backend.routers.protected_router import router as protected_router
from routers.threads_router import router as thread_router

from middlewares.auth_middlewares import AuthMiddleware

app = FastAPI(
    title="Chatbot API",
    version="1.0.0"
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allow the Vite dev server (port 5173) and any localhost origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth middleware ───────────────────────────────────────────────────────────
app.add_middleware(AuthMiddleware)

app.include_router(auth_router)
# app.include_router(protected_router)
app.include_router(user_router)
app.include_router(test_upload_router)
app.include_router(thread_router)


@app.get("/")
async def root():
    return {
        "message": "Chatbot Backend Running"
    }
