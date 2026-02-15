import requests
from bs4 import BeautifulSoup
import json
import os
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoldStandardScraper:
    def __init__(self):
        self.url = "https://www.techgearlab.com/topics/health-fitness/best-massage-gun"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # Metrics to pull from the techgearlab comparison matrix
        self.target_attributes = {
            "Measured Amplitude": "amplitude",
            "Measured Stall Force": "stall_force",
            "Measured Maximum PPM/Stroke": "max_ppm",
            "Measured Weight": "weight",
            "Maximum Measured Sound Range": "sound_range",
            "Price": "price"
        }

    def _clean_price(self, raw_text):
        if not raw_text: return None
        # Extract first currency pattern ($650)
        match = re.search(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', raw_text)
        return match.group(0) if match else raw_text

    def scrape_and_transpose(self):
        logger.info(f"Accessing live DOM at: {self.url}")
        try:
            response = requests.get(self.url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to fetch page: {e}")
            return []

        # Find the product comparison table
        table = soup.find('table', id='compare') or soup.find('table', class_=re.compile('compare', re.I))
        if not table:
            logger.error("Comparison table not found in the DOM.")
            return []

        products = []
        name_containers = table.select('div.compare_product_name')

        for container in name_containers:
            name = container.get_text(strip=True)
            if name:
                products.append({"brand_model": name})

        num_products = len(products)
        logger.info(f"Detected {num_products} products in the comparison matrix.")

        # Map row metrics back to the corresponding product column
        rows = table.find_all('tr')
        for row in rows:
            header_cell = row.find(['th', 'td'], class_=re.compile('compare_names', re.I))
            if not header_cell:
                continue

            header_text = header_cell.get_text(strip=True)
            attribute_key = None

            for target_name, key in self.target_attributes.items():
                if target_name.lower() in header_text.lower():
                    attribute_key = key
                    break

            if attribute_key:
                data_cells = row.find_all('td', class_=re.compile('compare_items', re.I))
                for i, cell in enumerate(data_cells):
                    if i < num_products:
                        raw_value = cell.get_text(strip=True)
                        if attribute_key == "price":
                            raw_value = self._clean_price(raw_value)
                        products[i][attribute_key] = raw_value

        return products

    def save(self, data, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding='utf-8') as f:
            count = 0
            for entry in data:
                # Save only if we actually got attributes
                if len(entry) > 1:
                    f.write(json.dumps(entry) + "\n")
                    count += 1
        logger.info(f"Successfully saved {count} gold standards to: {output_path}")


if __name__ == "__main__":
    # Resolve project root relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../../"))
    save_path = os.path.join(project_root, "data", "raw", "gold_standards.jsonl")

    scraper = GoldStandardScraper()
    final_data = scraper.scrape_and_transpose()

    if final_data:
        scraper.save(final_data, save_path)