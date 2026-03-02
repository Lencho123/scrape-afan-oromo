# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient 
MONGO_URL ="mongodb+srv://wako:scraper@cluster0scrpa.bvybm2w.mongodb.net/?appName=Cluster0Scrpa"

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