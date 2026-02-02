"""
UTILITY: Price Enrichment via Rainforest API
STATUS: ARCHIVED / REFERENCE ONLY
CONTEXT:
Developed to address 84% price sparsity in the raw Health & Household metadata.
Found that ~70% of missing entries were discontinued/dead listings as of 2026.
This script remains as a template for live-pricing integration in production.
"""

import json
import os
import requests
import time
import logging
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIG ---
API_KEY = os.getenv("RAINFOREST_KEY")
BASE_URL = "https://api.rainforestapi.com/request"


def recover_missing_prices(input_path, output_path, limit=100):
    """
    Identifies items with null prices and fetches them via Rainforest API.
    """
    # 1. Load your existing 1,603 products
    items = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            items.append(json.loads(line))

    # 2. Identify the 'Recovery List' (items without price)
    # We sort by rating_number descending so we prioritize "Famous" products
    to_recover = [item for item in items if item.get('price') is None]
    to_recover.sort(key=lambda x: x.get('rating_number', 0), reverse=True)

    already_good = [item for item in items if item.get('price') is not None]

    logger.info(f"Prioritizing recovery for high-volume products...")

    for i, item in enumerate(to_recover[:limit]):
        asin = item.get('parent_asin')

        params = {
            'api_key': API_KEY,
            'type': 'product',
            'amazon_domain': 'amazon.com',
            'asin': asin
        }

        try:
            response = requests.get(BASE_URL, params=params)
            data = response.json()

            if data.get('request_info', {}).get('success'):
                product = data.get('product', {})
                # Rainforest usually returns price in a structured 'price' object
                price_info = product.get('buybox_winner', {}).get('price', {})
                new_price = price_info.get('value')

                if new_price:
                    item['price'] = float(new_price)
                    recovered_count += 1
                    logger.info(f"[{i + 1}] Recovered ${new_price} for ASIN: {asin}")
                else:
                    logger.warning(f"[{i + 1}] No price found in API for {asin}")

            # Respect the free tier rate limits (Rainforest is fast, but be polite)
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"Error fetching {asin}: {e}")

    # 3. Combine and save
    final_dataset = already_good + to_recover
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in final_dataset:
            f.write(json.dumps(item) + '\n')

    logger.info(f"Recovery complete. Total items with price now: {len(already_good) + recovered_count}")


if __name__ == "__main__":
    # Standard path boilerplate
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../../"))

    data_in = os.path.join(project_root, "data", "processed", "amazon_hardware_refined.jsonl")

    # Run a test batch of 100 first
    recover_missing_prices(data_in, data_in, limit=100)