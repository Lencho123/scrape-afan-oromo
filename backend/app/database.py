# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient 
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

if not MONGO_URL:
    raise ValueError("MONGO_URL is not set in the environment variables")


# 1. Async Client (For FastAPI routes/frontend)
client = AsyncIOMotorClient(MONGO_URL)
database= client["facebook_scraper"]
posts_collection = database.get_collection("posts")

# ADD THIS for your Scraper
sync_client = MongoClient(MONGO_URL)
sync_db = sync_client["facebook_scraper"]
sync_posts_collection = sync_db.get_collection("posts")

async def init_db():
    await posts_collection.create_index("post_id", unique=True)