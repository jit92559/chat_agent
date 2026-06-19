import os
from dotenv import load_dotenv
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from langgraph.checkpoint.mongodb import MongoDBSaver
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
CHECK_DB=os.getenv("CHECK_DB")


sync_client = MongoClient(MONGO_URL)


def get_checkpointer():
    return MongoDBSaver(
        sync_client,
        db_name=CHECK_DB,
    )


users_collection = db["users"]
file_uploads_collection = db["file_uploads"]
threads_collection = db["threads"]
memory_collection = db["longterm_memories"]
# messages_collection=db['messages']