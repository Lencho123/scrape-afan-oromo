import asyncio
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from app.database import posts_collection
from app.models.schemas import PostSchema, CommentSchema
from datetime import datetime
import time

logger = logging.getLogger(__name__)

async def scrape_facebook_post(url: str, post_id: str):
    logger.info(f"Starting scrape for URL: {url} with ID: {post_id}")

    try:
        async with async_playwright() as p:

            # 🔹 Launch browser (set headless=False for debugging)
            browser = await p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )

            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            )

            page = await context.new_page()

            # 🔹 Navigate properly (wait for full load)
            await page.goto(url, wait_until="networkidle")

            # Small human-like delay
            await page.wait_for_timeout(3000)

            # 🔹 Handle cookie popup (if exists)
            try:
                await page.get_by_role("button", name="Allow all cookies").click(timeout=3000)
                await page.wait_for_timeout(2000)
            except:
                pass

            # 🔹 Try closing login popup (if appears)
            try:
                close_button = await page.wait_for_selector('div[aria-label="Close"]', timeout=3000)
                if close_button:
                    await close_button.click()
                    await page.wait_for_timeout(1000)
            except:
                pass

            # ===============================
            # ✅ EXTRACT POST TEXT
            # ===============================
            post_text = ""

            try:
                post_elements = page.locator('div[data-ad-comet-preview="message"] div[dir="auto"]')
                count = await post_elements.count()

                texts = []
                for i in range(count):
                    txt = await post_elements.nth(i).inner_text()
                    if txt:
                        texts.append(txt)

                post_text = "\n".join(texts)

            except Exception as e:
                logger.error(f"Post text extraction failed: {e}")

            if not post_text:
                post_text = "Could not extract post text"

            # ===============================
            # ✅ SCROLL TO LOAD COMMENTS
            # ===============================
            max_scrolls = 8
            for _ in range(max_scrolls):
                await page.mouse.wheel(0, 1500)
                await page.wait_for_timeout(1500)

                # Click "View more comments" if exists
                more_buttons = page.locator('div[role="button"]:has-text("View more comments")')
                if await more_buttons.count() > 0:
                    try:
                        await more_buttons.first.click()
                        await page.wait_for_timeout(2000)
                    except:
                        pass

            # Wait until comments appear
            try:
                await page.wait_for_selector('div[role="article"]', timeout=10000)
            except:
                logger.warning("No comment articles found.")

            # ===============================
            # ✅ EXTRACT COMMENTS
            # ===============================
            comments = []
            seen_texts = set()

            comment_elements = page.locator('div[role="article"]')
            total_comments = await comment_elements.count()

            logger.info(f"Found {total_comments} comment blocks.")

            for i in range(total_comments):
                try:
                    element = comment_elements.nth(i)

                    text_locator = element.locator('div[dir="auto"]').first
                    text = await text_locator.inner_text()

                    if text and text not in seen_texts and len(text) > 2:
                        seen_texts.add(text)

                        comments.append(
                            CommentSchema(
                                text=text.strip(),
                                date=datetime.now().strftime("%Y-%m-%d")
                            )
                        )

                except:
                    continue

            # ===============================
            # ✅ SAVE TO DATABASE
            # ===============================
            post_data = PostSchema(
                post_id=post_id,
                post_text=post_text,
                post_date=datetime.now().strftime("%Y-%m-%d"),
                comments=comments
            )

            await posts_collection.insert_one(post_data.dict())

            logger.info(f"Successfully scraped and saved post: {post_id}")

            await browser.close()

    except Exception as e:
        logger.error(f"Scrape failed for {url}: {str(e)}")

        await posts_collection.insert_one(
            PostSchema(
                post_id=post_id,
                post_text=f"Failed to scrape: {str(e)}",
                post_date=datetime.now().strftime("%Y-%m-%d"),
                comments=[]
            ).dict()
        )