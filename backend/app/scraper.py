import logging
import sys
import os
import json
import time
from playwright.sync_api import sync_playwright
from app.database import posts_collection
from app.models.schemas import PostSchema, CommentSchema
from datetime import datetime
import asyncio
from app.database import sync_posts_collection

logger = logging.getLogger(__name__)

# --- 1. THE COOKIE SANITIZER ---
def sanitize_cookies(cookies_list):
    valid_samesite = ["Strict", "Lax", "None"]
    cleaned_cookies = []
    for cookie in cookies_list:
        # Fix SameSite issues
        if cookie.get('sameSite') not in valid_samesite:
            cookie['sameSite'] = 'Lax'
        
        # Rename expirationDate to expires
        if 'expirationDate' in cookie:
            cookie['expires'] = cookie.pop('expirationDate')
            
        # Fix PartitionKey issues
        if "partitionKey" in cookie and not isinstance(cookie["partitionKey"], str):
            del cookie["partitionKey"]
            
        # Remove internal keys that Playwright rejects
        for key in ['hostOnly', 'session', 'storeId', 'id']:
            cookie.pop(key, None)
        cleaned_cookies.append(cookie)
    return cleaned_cookies

# --- 2. THE SYNC SCRAPER ---
def scrape_facebook_post(url: str, post_id: str):
    url = str(url)
    logger.info(f"🚀 Starting Sync Scrape: {post_id}")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cookies_path = os.path.join(current_dir, "cookies.json")
    
    with sync_playwright() as p:
        browser = None
        try:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )

            # Cookie Injection
            if os.path.exists(cookies_path):
                with open(cookies_path, 'r') as f:
                    raw_cookies = json.load(f)
                    context.add_cookies(sanitize_cookies(raw_cookies))
                logger.info("✅ Cookies sanitized and injected")

            page = context.new_page()
            
            # Navigate
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(5) 

            # Extract Post Content
            post_text = "Could not extract text"
            content_selector = 'div[data-ad-preview="message"]'
            
            if page.locator(content_selector).count() > 0:
                post_text = page.locator(content_selector).first.inner_text()

            # Extract Comments
            page.mouse.wheel(0, 1000)
            time.sleep(2)
            
            comments = []
            comment_elements = page.locator('div[role="article"] div[dir="auto"]')
            count = comment_elements.count()
            
            for i in range(min(count, 10)):
                txt = comment_elements.nth(i).inner_text()
                if txt and len(txt) > 2:
                    comments.append(CommentSchema(
                        text=txt.strip(), 
                        date=datetime.now().strftime("%Y-%m-%d")
                    ).dict()) # Use .dict() for database safety

            # Database Update (We use a standard call here)
            # Since this is a thread, we use the collection directly
            data_to_save = {
                "post_id": post_id,
                "post_text": post_text,
                "post_date": datetime.now().strftime("%Y-%m-%d"),
                "comments": comments
            }

            # Note: If your posts_collection is a Motor (async) collection, 
            # you may need a small bridge, but usually, simple background threads 
            # can handle this via the motor client.
            
            sync_posts_collection.update_one(
                {"post_id": post_id},
                {"$set": data_to_save},
                upsert=True
            )
            
            logger.info(f"🎉 Success: {post_id} saved.")

        except Exception as e:
            logger.error(f"❌ Scraper Failed: {str(e)}")
        finally:
            if browser:
                browser.close()