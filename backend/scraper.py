from playwright.sync_api import sync_playwright
try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None
import urllib.parse
import time
import random
from backend.utils.logger import logger

class MarketplaceScraper:
    def __init__(self, advisor):
        self.advisor = advisor

    def search_google(self, artist, album, headless=False):
        """Executes a Google search for Dutch vinyl shops and visits top results"""
        query = urllib.parse.quote(f"{artist} {album} vinyl nl")
        url = f"https://www.google.com/search?q={query}&hl=nl"

        results = []
        try:
            with sync_playwright() as p:
                logger.scrape(f"Launching scraper (Headless={headless}) for Google Search: {url}")
                browser = p.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])

                # Use a modern user agent to avoid bot detection
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                context = browser.new_context(user_agent=user_agent)
                page = context.new_page()

                # Apply stealth if available
                if stealth_sync:
                    stealth_sync(page)

                # Small random delay to simulate human lead-in
                time.sleep(random.uniform(1.5, 3.5))

                page.goto(url, wait_until="networkidle", timeout=30000)

                # Handle cookie consent if it appears (common in NL)
                try:
                    # Generic selector for 'Accept All' buttons in Dutch
                    consent_button = page.locator('button:has-text("Alles accepteren"), button:has-text("Akkoord")').first
                    if consent_button.is_visible(timeout=3000):
                        time.sleep(random.uniform(0.5, 1.2))
                        consent_button.click()
                except:
                    pass

                # Extract top organic shop links from Google results using more robust selectors
                links = page.evaluate("""() => {
                    // Look for organic result links (usually inside h3 or specifically marked divs)
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
                        page.goto(link, wait_until="domcontentloaded", timeout=15000)
                        # Extract raw text content for the LLM to parse
                        text = page.evaluate("() => document.body.innerText")
                        results.append({
                            "site": link.split('/')[2],
                            "url": link,
                            "raw_content": text[:6000] # Truncate to save tokens while keeping context
                        })
                    except Exception as e:
                        logger.error(f"Failed to scrape {link}: {e}")

                browser.close()
        except Exception as e:
            logger.error(f"Google Scraper encountered an error: {e}")

        return results

    def get_links(self, artist, album, headless=True):
        """Orchestrates Google search and uses LLM to extract JSON structured store data"""
        raw_data = self.search_google(artist, album, headless=headless)
        if not raw_data:
            return []
        # print(raw_data)
        logger.ai("Sending raw marketplace data to LLM for parsing...")
        return self.advisor.parse_scraper_results(artist, album, raw_data)