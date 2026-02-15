import json
import os
import requests
import logging

# Professional logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clean_price(price_val):
    """Convert price strings to floats. Essential for ML distance calculations."""
    if not price_val:
        return None
    try:
        # Strip symbols and convert to float for calculations
        return float(str(price_val).replace('$', '').replace(',', '').strip())
    except ValueError:
        return None


def stream_and_filter_hardware(output_path):
    """
    Sifts through the 11GB+ McAuley Lab Amazon dataset to find massage guns.
    Filters out noise like supplements, chargers, and sexual wellness items.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    url = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw/meta_categories/meta_Health_and_Household.jsonl"

    include_keywords = ["massage gun", "percussive", "percussion massage", "massage pistol"]

    # These categories frequently hijack the search results
    exclude_list = [
        "protein", "powder", "supplement", "amino", "creatine", "whey", "capsules", "oil", "cream", "gel", "lotion",
        "foam roller", "yoga mat", "attachment", "replacement head", "massage head", "carrying case", "charger only",
        "her pleasure", "vibrator", "wand massager", "magic massage", "sex toy", "clitorial"
        ]

    count = 0
    total_scanned = 0

    logger.info("Starting stream from HuggingFace...")

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(output_path, 'w', encoding='utf-8') as f:
            for line in response.iter_lines():
                if line:
                    total_scanned += 1
                    item = json.loads(line)

                    # Check title and features for hardware indicators
                    title = str(item.get('title') or "").lower()
                    features_list = item.get('features') or []
                    desc_list = item.get('description') or []
                    content = f"{title} {' '.join(features_list)} {' '.join(desc_list)}".lower()

                    if any(kw in content for kw in include_keywords):
                        if not any(ex in content for ex in exclude_list):
                            # Save a cleaned subset of the metadata
                            clean_item = {
                                "parent_asin": item.get("parent_asin"),
                                "title": item.get('title'),
                                "store": item.get('store'),
                                "price": clean_price(item.get("price")),
                                "average_rating": float(item.get("average_rating")) if item.get(
                                    "average_rating") else None,
                                "rating_number": int(item.get("rating_number")) if item.get("rating_number") else 0,
                                "features": features_list,
                                "description": desc_list,
                                "details": item.get('details'),
                                "categories": item.get('categories'),
                                #"images": item.get('images'),
                                #"bought_together": item.get('bought_together')
                            }
                            f.write(json.dumps(clean_item) + '\n')
                            count += 1

                if total_scanned % 10000 == 0:
                    logger.info(f"Scanned {total_scanned} items, found {count} potential guns")

    except Exception as e:
        logger.error(f"Stream failed: {e}")

    logger.info(f"Done. Saved {count} products.")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../../"))
    save_path = os.path.join(project_root, "data", "raw", "amazon_market_raw.jsonl")

    if os.path.exists(save_path):
        os.remove(save_path)
        logger.info("Purging old data for clean ingestion.")

    stream_and_filter_hardware(save_path)