import json
import os
import requests
import logging

# Professional logging setup instead of just print statements
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def stream_and_filter_recovery_data(output_path):
    """
    Streams 11GB+ Amazon Metadata from McAuley Lab and filters for recovery hardware.
    Saves results directly to data/processed for downstream classification.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    url = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw/meta_categories/meta_Health_and_Household.jsonl"
    keywords = ["massage gun", "percussive", "foam roller", "compression boots", "muscle recovery"]
    count = 0
    total_scanned = 0

    logger.info(f"Production Streamer Started: Targeting {url.split('/')[-1]}")

    try:
        # stream=True prevents memory overflow with massive datasets
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(output_path, 'w', encoding='utf-8') as f:
            for line in response.iter_lines():
                if line:
                    total_scanned += 1
                    try:
                        item = json.loads(line)

                        title = str(item.get('title') or "")
                        features = item.get('features') or []
                        content = (title + " " + " ".join(features)).lower()

                        if any(kw in content for kw in keywords):
                            clean_item = {
                                "parent_asin": item.get("parent_asin"),
                                "title": title,
                                "features": features,
                                "price": str(item.get("price") or ""),
                                "average_rating": item.get("average_rating"),
                                "store": item.get("store")
                            }
                            f.write(json.dumps(clean_item) + '\n')
                            count += 1

                            if count % 500 == 0:
                                logger.info(f"Captured {count} items (Scanned: {total_scanned:,})")

                    except json.JSONDecodeError:
                        continue

    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        return

    logger.info(f"Success! Captured {count:,} items from {total_scanned:,} total products.")
    logger.info(f"File saved to: {output_path}")


if __name__ == "__main__":
    # 1. Dynamically find the project root (strategic-discovery-engine)
    # This makes the script location-agnostic
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../../"))

    # 2. Set path to root > data > processed
    save_path = os.path.join(project_root, "data", "processed", "amazon_recovery_items.jsonl")

    stream_and_filter_recovery_data(save_path)