import logging
import sys
import os
import json
import time
import re
from playwright.sync_api import sync_playwright
from app.database import sync_posts_collection
from app.models.schemas import CommentSchema
from datetime import datetime

logger = logging.getLogger(__name__)

# --- 1. CLEANER LOGIC ---
def clean_text(text: str) -> str:
    if not text:
        return ""
    # 1. Remove the '#' character
    text = text.replace('#', '')
    
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+|www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    text = re.sub(url_pattern, '', text)
    # 2. Collapse multiple whitespaces/newlines into a single space
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned

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

            # --- NAVIGATION ---
            logger.info(f"🌐 Navigating to URL: {url}")
            page.goto(url, wait_until="networkidle", timeout=90000)
            page.wait_for_timeout(5000)

            # --- STEP 1: 'ALL COMMENTS' FILTER ---
            try:
                filter_selector = 'div[role="button"]:has-text("Most relevant"), div[role="button"]:has-text("Top comments")'
                filter_btn = page.locator(filter_selector).first
                if filter_btn.is_visible(timeout=5000):
                    filter_btn.click()
                    page.wait_for_timeout(2000)
                    page.locator('div[role="menuitem"] >> span:has-text("All comments")').click()
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(3000)
            except:
                logger.info("ℹ️ Filter switch skipped.")

            # --- STEP 2: AGGRESSIVE EXPANSION ---
            logger.info("🖱️ Deep expanding content...")
            last_height = 0
            for i in range(40): 
                # Expand main comment lists
                view_more = page.locator('div[role="button"]:has-text("View more comments"), span:has-text("View previous comments")').first
                if view_more.is_visible():
                    view_more.click()
                    page.wait_for_timeout(2500)
                
                # Expand truncated "See more" text in comments
                see_mores = page.locator('div[role="article"] div[role="button"]:has-text("See more")').all()
                for sm in see_mores:
                    try:
                        if sm.is_visible():
                            sm.click(timeout=1000)
                            page.wait_for_timeout(500)
                    except: pass
                
                # Scroll to trigger lazy loading of Virtual DOM
                page.mouse.wheel(0, 3000)
                page.wait_for_timeout(2000)
                
                curr_height = page.evaluate("document.body.scrollHeight")
                if curr_height == last_height and i > 10:
                    break
                last_height = curr_height

            # --- STEP 3: TARGETED EXTRACTION ---
            msg_selector = 'div[data-ad-preview="message"]'
            raw_post_text = page.locator(msg_selector).first.inner_text().strip() if page.locator(msg_selector).count() > 0 else ""
            post_text = clean_text(raw_post_text)

            comments_data = []
            seen_hashes = set()

            # Extract from individual article blocks to keep comments separate from post
            articles = page.locator('div[role="article"]').all()
            
            for article in articles:
                # Skip if this article block contains the main post message
                if article.locator(msg_selector).count() > 0:
                    continue

                # Target the comment body
                text_node = article.locator('div[dir="auto"]').first
                if text_node.count() == 0:
                    continue

                text_node.scroll_into_view_if_needed()
                raw_txt = text_node.inner_text().strip()
                txt = clean_text(raw_txt)
                
                # Filter UI noise and duplicates
                if not txt or len(txt) < 2 or txt == post_text:
                    continue
                if txt.isdigit():
                    continue
                
                if contains_amharic(txt):
                    continue
                # Skip if text is only one letter (e.g. "f", "A")
                if len(txt) == 1 and txt.isalpha():
                    continue
                
                if txt in ["Like", "Reply", "Share", "See more", "Write a comment..."]:
                    continue

                txt_hash = hash(txt)
                if txt_hash in seen_hashes:
                    continue
                
                comment_obj = CommentSchema(
                    text=txt, 
                    date=datetime.now().strftime("%Y-%m-%d")
                )
                comments_data.append(comment_obj.model_dump() if hasattr(comment_obj, 'model_dump') else comment_obj.dict())
                seen_hashes.add(txt_hash)

            # --- STEP 4: DATABASE UPDATE ---
            data_to_save = {
                "post_id": post_id,
                "url": url,
                "post_text": post_text,
                "post_date": datetime.now().strftime("%Y-%m-%d"),
                "comments": comments_data,
                "updated_at": datetime.now().isoformat(),
                "status": "completed"
            }

            sync_posts_collection.update_one(
                {"post_id": post_id},
                {"$set": data_to_save},
                upsert=True
            )
            logger.info(f"🎉 Success: Found {len(comments_data)} unique comments.")

        except Exception as e:
            logger.error(f"❌ Scraper Critical Error: {str(e)}")
        finally:
            if browser:
                browser.close()
                logger.info("🔒 Browser session ended.")
                