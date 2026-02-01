import requests
from bs4 import BeautifulSoup
import logging
import time
from datetime import datetime

# Set up professional logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RecoveryScraper:
    """
    Standardized scraper for high-end recovery devices.
    Designed for modularity and resilience against UI changes.
    """

    def __init__(self, headers=None):
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }

    def fetch_page(self, url):
        """Fetches HTML with professional error handling and timeouts."""
        try:
            time.sleep(1)  # Basic rate limiting to be a 'good bot'
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {url}: {e}")
            return None

    def _extract_spec_by_keyword(self, soup, keyword):
        """
        Helper to find specs in messy HTML by searching for specific labels.
        This is more resilient than hard-coded CSS paths.
        """
        # Look for the keyword in any tag, then find its nearest value
        element = soup.find(lambda tag: tag.name in ['dt', 'span', 'div', 'th'] and keyword in tag.get_text())
        if element:
            # Often the value is in the next sibling or a parent's child
            value = element.find_next(['dd', 'span', 'div', 'td'])
            return value.get_text(strip=True) if value else None
        return None

    def scrape_product(self, url, brand="generic"):
        """Main entry point for scraping any recovery product."""
        html = self.fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Standardized schema for the 'Item Tower'
        specs = {
            "brand": brand,
            "url": url,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amplitude_mm": self._extract_spec_by_keyword(soup, "Amplitude"),
            "stall_force_lbs": self._extract_spec_by_keyword(soup, "Stall Force"),
            "ppm_max": self._extract_spec_by_keyword(soup, "Percussions"),
            "battery_life": self._extract_spec_by_keyword(soup, "Battery")
        }

        logger.info(f"Successfully scraped specs for: {url}")
        return specs


if __name__ == "__main__":
    scraper = RecoveryScraper()
    # Testing with a known gold-standard device
    test_url = "https://www.therabody.com/products/theragun-pro-plus"
    product_data = scraper.scrape_product(test_url, brand="Therabody")
    if product_data:
        print("\n--- Scraped Data ---")
        for key, value in product_data.items():
            print(f"{key.upper()}: {value}")
    else:
        print("Scrape failed. Check logs for error details.")