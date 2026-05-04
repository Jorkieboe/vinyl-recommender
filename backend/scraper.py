import asyncio
from playwright.async_api import async_playwright
try:
    from playwright_stealth import stealth_async as stealth
except ImportError:
    stealth = None
import urllib.parse
import time
import random
from backend.utils.logger import logger

class MarketplaceScraper:
    def __init__(self, advisor):
        self.advisor = advisor

    async def search_google(self, artist, album, headless=False):
        """Executes an asynchronous Google search for Dutch vinyl shops and visits top results"""
        query = urllib.parse.quote(f"{artist} {album} vinyl nl")
        url = f"https://www.google.com/search?q={query}&hl=nl"

        logger.scrape(f"Start scraping on {url}")

        results = []
        try:
            async with async_playwright() as p:
                logger.scrape(f"Launching async scraper (Headless={headless}) for Google Search: {url}")
                browser = await p.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])

                # Use a modern user agent to avoid bot detection
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                context = await browser.new_context(user_agent=user_agent)
                page = await context.new_page()

                # Apply stealth if available
                if stealth:
                    await stealth(page)

                # Small random delay to simulate human lead-in
                await asyncio.sleep(random.uniform(1.5, 3.5))

                await page.goto(url, wait_until="networkidle", timeout=30000)

                try:
                    consent_button = page.locator('button:has-text("Alles accepteren"), button:has-text("Akkoord")').first
                    if await consent_button.is_visible(timeout=3000):
                        await asyncio.sleep(random.uniform(0.5, 1.2))
                        await consent_button.click()
                except:
                    pass

                links = await page.evaluate("""() => {
                    const organicSelectors = ['#search a', 'div.g a', 'a[data-ved]'];
                    let anchors = [];
                    organicSelectors.forEach(sel => {
                        anchors = anchors.concat(Array.from(document.querySelectorAll(sel)));
                    });

                    return anchors.map(a => a.href)
                        .filter(href => {
                            try {
                                const u = new URL(href);
                                return !u.hostname.includes('google') &&
                                       !u.hostname.includes('youtube') &&
                                       !u.hostname.includes('facebook') &&
                                       !u.hostname.includes('instagram') &&
                                       href.startsWith('http');
                            } catch { return false; }
                        })
                        .filter((v, i, a) => a.indexOf(v) === i) // unique only
                        .slice(0, 3);
                }""")

                # Deep scrape the actual product pages to find price/stock details
                for link in links:
                    logger.scrape(f"Scraping product page: {link}")
                    try:
                        await page.goto(link, wait_until="domcontentloaded", timeout=15000)
                        # Extract raw text content for the LLM to parse
                        text = await page.evaluate("() => document.body.innerText")
                        results.append({
                            "site": link.split('/')[2],
                            "url": link,
                            "raw_content": text[:6000] # Truncate to save tokens while keeping context
                        })
                    except Exception as e:
                        logger.error(f"Failed to scrape {link}: {e}")

                await browser.close()
        except Exception as e:
            logger.error(f"Google Scraper encountered an error: {e}")

        return results

    async def get_links(self, artist, album, headless=True):
        """Orchestrates Google search and uses LLM to extract JSON structured store data (Async)"""
        raw_data = await self.search_google(artist, album, headless=headless)
        if not raw_data:
            return []

        logger.ai("Sending raw marketplace data to LLM for parsing...")
        return await self.advisor.parse_scraper_results(artist, album, raw_data)