from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from fastapi.concurrency import run_in_threadpool

from configs.auth_config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from configs.db_config import users_collection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def hash_password(password: str):
    return await run_in_threadpool(
        pwd_context.hash,
        password,
    )


async def verify_password(plain_password: str, hashed_password: str):
    return await run_in_threadpool(
        pwd_context.verify,
        plain_password,
        hashed_password,
    )


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def register_user(name: str, email: str, password: str):
    existing_user = await users_collection.find_one({"email": email})

    if existing_user:
        return None

    hashed_password = await hash_password(password)

    user = {
        "name": name,
        "email": email,
        "password": hashed_password,
        "created_at": datetime.now(timezone.utc),
    }

    result = await users_collection.insert_one(user)
    user["_id"] = str(result.inserted_id)

    return user


async def authenticate_user(email: str, password: str):
    user = await users_collection.find_one({"email": email})

    if not user:
        return None

    is_valid = await verify_password(password, user["password"])

    if not is_valid:
        return None

    user["_id"] = str(user["_id"])
    return user


async def get_user_by_email(email: str):
    user = await users_collection.find_one({"email": email})

    if not user:
        return None

    user["_id"] = str(user["_id"])
    return user