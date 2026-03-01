import asyncio
import sys
import uuid
from starlette.concurrency import run_in_threadpool # Essential for the fix
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .scraper import scrape_facebook_post
from app.database import init_db
from app.models.schemas import ScrapeRequest
from app.api import router as api_router

# 1. Force the policy globally at the very top
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@asynccontextmanager
async def lifespan(app: FastAPI):
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    await init_db()
    yield

app = FastAPI(title="Facebook Scraper API", lifespan=lifespan)

# Middleware and Router
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")

# --- THE FIX: SYNC WRAPPER ---
def sync_wrapper(url: str, post_id: str):
    """
    This runs in a separate thread. asyncio.run() creates a 
    completely fresh Event Loop that doesn't inherit Uvicorn's 
    restrictions, allowing Playwright to start subprocesses.
    """
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    return asyncio.run(scrape_facebook_post(url, post_id))

@app.post("/api/scrape")
async def trigger_scrape(data: ScrapeRequest, background_tasks: BackgroundTasks):
    # CRITICAL: Force the URL to be a plain string here
    url_str = str(data.url) 
    
    post_id = data.post_id or str(uuid.uuid4())
    
    # Pass the plain string 'url_str', NOT 'data.url'
    background_tasks.add_task(scrape_facebook_post, url_str, post_id)
    
    return {"status": "accepted", "post_id": post_id}
@app.get("/")
def read_root():
    return {"message": "API is online"}