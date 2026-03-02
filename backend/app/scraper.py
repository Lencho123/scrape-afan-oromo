import logging
import sys
import os
import json
import time
import re
import dateparser
from playwright.sync_api import sync_playwright
from app.database import sync_posts_collection
from app.models.schemas import CommentSchema
from datetime import datetime

logger = logging.getLogger(__name__)

# --- 1. CLEANER LOGIC ---
import re

def clean_and_validate_text(text: str) -> str:
    if not text:
        return ""
    
    # --- EXISTING CLEANING LOGIC ---
    text = re.sub(r'<.*?>', '', text) # HTML
    text = re.sub(r'\S+@\S+\.\S+', '', text) # Emails
    text = re.sub(r'@\w+', '', text) # Mentions
    text = re.sub(r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}', '', text) # Phone
    
    # Remove extra spaces/newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    # --- TWO WORD VALIDATION ---
    # Split by whitespace and filter out empty strings
    words = [w for w in text.split(' ') if w]
    
    if len(words) < 2:
        return "" # Discard text that is too short
        
    return text
def contains_amharic(text: str) -> bool:
    """Returns True if the text contains characters from the Ethiopic Unicode block."""
    # Ethiopic Unicode Range: \u1200-\u137F
    amharic_pattern = re.compile(r'[\u1200-\u137F]')
    return bool(amharic_pattern.search(text))
# --- 2. COOKIE HELPER (FIXES THE CRASH) ---
def sanitize_cookies(cookies_list):
    valid_samesite = ["Strict", "Lax", "None"]
    cleaned_cookies = []
    for cookie in cookies_list:
        # FIX: Ensure partitionKey is a string or deleted to prevent Playwright crash
        if "partitionKey" in cookie:
            if not isinstance(cookie["partitionKey"], str):
                del cookie["partitionKey"]
        
        if cookie.get('sameSite') not in valid_samesite:
            cookie['sameSite'] = 'Lax'
            
        if 'expirationDate' in cookie:
            cookie['expires'] = int(cookie.pop('expirationDate'))
            
        for key in ['hostOnly', 'session', 'storeId', 'id']:
            cookie.pop(key, None)
            
        cleaned_cookies.append(cookie)
    return cleaned_cookies

# --- 3. THE FINAL SCRAPER ---
def scrape_facebook_post(url: str, post_id: str):
    url = str(url)
    logger.info(f"🚀 Starting Deep Scrape: {post_id}")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cookies_path = os.path.join(current_dir, "cookies.json")
    
    # Check if already exists to save resources
    if sync_posts_collection.find_one({"post_id": post_id}):
        return {"status": "skipped", "message": "Post already in database."}

    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 1200},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )

            if os.path.exists(cookies_path):
                with open(cookies_path, 'r') as f:
                    raw_cookies = json.load(f)
                    context.add_cookies(sanitize_cookies(raw_cookies))

            page = context.new_page()
            logger.info(f"🌐 Navigating to URL: {url}")
            page.goto(url, wait_until="networkidle", timeout=90000)
            page.wait_for_timeout(5000)

            # --- STEP 1: LOAD ALL COMMENTS ---
            try:
                filter_selector = 'div[role="button"]:has-text("Most relevant"), div[role="button"]:has-text("Top comments")'
                filter_btn = page.locator(filter_selector).first
                if filter_btn.is_visible(timeout=5000):
                    filter_btn.click()
                    page.wait_for_timeout(2000)
                    page.locator('div[role="menuitem"] >> span:has-text("All comments")').click()
                    page.wait_for_timeout(3000)
            except:
                logger.info("ℹ️ Filter switch skipped.")

            # --- STEP 2: EXPAND ---
            last_height = 0
            for i in range(25): # Loop to scroll and click 'View more'
                view_more = page.locator('div[role="button"]:has-text("View more comments"), span:has-text("View previous comments")').first
                if view_more.is_visible():
                    view_more.click()
                    page.wait_for_timeout(2000)
                
                page.mouse.wheel(0, 2000)
                curr_height = page.evaluate("document.body.scrollHeight")
                if curr_height == last_height: break
                last_height = curr_height

            # --- STEP 3: EXTRACTION ---
            msg_selector = 'div[data-ad-preview="message"]'
            raw_post_text = page.locator(msg_selector).first.inner_text().strip() if page.locator(msg_selector).count() > 0 else ""
            post_text = clean_and_validate_text(raw_post_text)

            # Date Logic
            final_formatted_date = datetime.now().strftime("%Y-%m-%d")
            try:
                timestamp_loc = page.locator('span[id] a[href*="posts"], a[role="link"] > span[dir="auto"]').first
                aria_label = timestamp_loc.get_attribute("aria-label")
                raw_date = aria_label if aria_label else timestamp_loc.inner_text()
                parsed_dt = dateparser.parse(raw_date)
                if parsed_dt:
                    final_formatted_date = parsed_dt.strftime("%Y-%m-%d")
            except: pass

            # Comment Logic: Store as simple list of strings
            comments_list = []
            seen_hashes = set()
            articles = page.locator('div[role="article"]').all()
            
            for article in articles:
                # Skip the main post itself if it's caught in the article role
                if article.locator(msg_selector).count() > 0: continue

                text_node = article.locator('div[dir="auto"]').first
                if text_node.count() == 0: continue

                raw_txt = text_node.inner_text().strip()
                txt = clean_and_validate_text(raw_txt)
                
                # Filters
                if not txt or len(txt) < 3 or txt == post_text: continue
                if contains_amharic(txt) or txt in ["Like", "Reply", "Share", "See more"]: continue

                txt_hash = hash(txt)
                if txt_hash not in seen_hashes:
                    comments_list.append(txt) # Store ONLY the string
                    seen_hashes.add(txt_hash)

            # --- STEP 4: DB SAVE ---
            data_to_save = {
                "post_id": post_id,
                "url": url,
                "post_text": post_text, # API will map this to 'post'
                "post_date": final_formatted_date, 
                "comments": comments_list, # Array of strings
                "updated_at": datetime.now().isoformat()
            }

            sync_posts_collection.update_one(
                {"post_id": post_id},
                {"$set": data_to_save},
                upsert=True
            )
            
            return {"status": "success", "message": f"Saved {len(comments_list)} comments."}

        except Exception as e:
            logger.error(f"❌ Scraper Error: {str(e)}")
            return {"status": "error", "message": str(e)}
        finally:
            if browser: browser.close()