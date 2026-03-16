import os
from typing import Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

# Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://CodingMaster:abcd1234@moni.cswjycu.mongodb.net/moni?appName=moni")
DB_NAME = "moni"

# Global database state
client: Optional[AsyncIOMotorClient] = None
db: Any = None


async def connect_db():
    "Connect to MongoDB and verify connection"
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        # Verify connection
        await client.admin.command("ping")
        db = client[DB_NAME]
        print("✅ MongoDB Connected Successfully!")
        print(f"   Database: {DB_NAME}")
    except Exception as e:
        print(f"⚠️ MongoDB Connection Warning: {e}")
        print("   The app will continue starting, but database features may be unavailable.")


async def close_db():
    "Close MongoDB connection"
    global client
    if client:
        client.close()
        print("MongoDB connection closed.")


def get_users_collection():
    "Helper to get the users collection"
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    return db["users"]


def get_drug_predictions_collection():
    "Helper to get the drug_predictions collection"
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    return db["drug_predictions"]


def get_analysis_history_collection():
    "Helper to get the analysis_history collection"
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    return db["analysis_history"]

