from playwright.sync_api import sync_playwright
import urllib.parse

class MarketplaceScraper:
    def __init__(self, advisor):
        self.advisor = advisor

    def search_velvet(self, artist, album):
        query = urllib.parse.quote(f"{artist} {album} vinyl")
        url = f"https://www.velvetmusic.nl/search/?q={query}"
        return self._scrape_site(url, "Velvet.nl")

    def search_bol(self, artist, album):
        query = urllib.parse.quote(f"{artist} {album} vinyl")
        url = f"https://www.bol.com/nl/nl/s/?searchtext={query}"
        return self._scrape_site(url, "Bol.com")

    def _scrape_site(self, url, site_name):
        try:
            with sync_playwright() as p:
                # Note: Requires 'playwright install chromium'
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)

                # Extract text content to help LLM parse it
                # We take a snapshot of the body text to avoid huge HTML payloads
                content = page.evaluate("() => document.body.innerText")
                browser.close()

                return {
                    "site": site_name,
                    "url": url,
                    "raw_content": content[:8000] # Truncate to save tokens
                }
        except Exception as e:
            print(f"Scraper error for {site_name}: {e}")
            return None

    def get_links(self, artist, album):
        """Orchestrates multiple scrapers and uses LLM to parse results"""
        raw_data = []

        # Velvet.nl
        v_res = self.search_velvet(artist, album)
        if v_res:
            raw_data.append(v_res)

        # Bol.com
        b_res = self.search_bol(artist, album)
        if b_res:
            raw_data.append(b_res)

        if not raw_data:
            return []

        return self.advisor.parse_scraper_results(artist, album, raw_data)