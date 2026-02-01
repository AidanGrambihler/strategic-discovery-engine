import json
import os
import requests
import logging

# Professional logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clean_price(price_val):
    """Convert price strings to floats. Essential for ML distance calculations."""
    if price_val is None or price_val == "" or price_val == "None":
        return None
    try:
        return float(str(price_val).replace('$', '').replace(',', '').strip())
    except ValueError:
        return None


def stream_and_filter_hardware(output_path):
    """
    Streams 11GB+ McAuley Lab metadata.
    Implements multi-stage filtering to isolate recovery hardware from supplements,
    attachment parts, and sexual wellness items.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    url = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw/meta_categories/meta_Health_and_Household.jsonl"

    # 1. POSITIVE SIGNAL: Hardware-centric
    include_keywords = ["massage gun", "percussive", "percussion massage", "massage pistol"]

    # 2. CATEGORY NOISE: Supplements & Manual Tools
    exclude_consumables = [
        "protein", "powder", "supplement", "amino", "creatine", "whey",
        "capsules", "oil", "cream", "gel", "lotion", "foam roller", "yoga mat"
    ]

    # 3. COMPONENT NOISE: Identifying listings for heads/attachments/cases ONLY
    exclude_attachments = ["attachment", "replacement head", "massage head", "carrying case", "charger only"]

    # 4. DOMAIN NOISE: Filtering sexual wellness items that hijack 'wand' or 'handheld' keywords
    exclude_sexual = ["her pleasure", "vibrator", "wand massager", "magic massage", "sex toy", "clitorial"]

    count = 0
    total_scanned = 0

    logger.info("Initializing V4 Precision Streamer: Hardware Arbitrage Target.")

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(output_path, 'w', encoding='utf-8') as f:
            for line in response.iter_lines():
                if line:
                    total_scanned += 1
                    try:
                        item = json.loads(line)

                        # Gather all text for deep inspection
                        title = str(item.get('title') or "").lower()
                        features_list = item.get('features') or []
                        desc_list = item.get('description') or []
                        content = f"{title} {' '.join(features_list)} {' '.join(desc_list)}".lower()

                        # Logic Gates
                        has_hardware = any(kw in content for kw in include_keywords)
                        is_consumable = any(ex in content for ex in exclude_consumables)
                        is_attachment = any(at in content for at in exclude_attachments)
                        is_sexual = any(sx in content for sx in exclude_sexual)

                        # We only keep it if it's Hardware AND NOT any of the noise categories
                        if has_hardware and not (is_consumable or is_attachment or is_sexual):

                            # Type Casting for ML Readiness
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
                                "images": item.get('images'),
                                "bought_together": item.get('bought_together')
                            }

                            f.write(json.dumps(clean_item) + '\n')
                            count += 1

                            if count % 500 == 0:
                                logger.info(f"Verified {count} Hardware Disruptors (Scanned: {total_scanned:,})")

                    except (json.JSONDecodeError, ValueError):
                        continue

    except Exception as e:
        logger.error(f"Stream interrupted: {e}")
        return

    logger.info(f"Capture Complete: {count:,} high-fidelity products isolated.")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../../"))
    save_path = os.path.join(project_root, "data", "processed", "amazon_hardware_refined.jsonl")

    if os.path.exists(save_path):
        os.remove(save_path)
        logger.info("Purging old data for clean ingestion.")

    stream_and_filter_hardware(save_path)