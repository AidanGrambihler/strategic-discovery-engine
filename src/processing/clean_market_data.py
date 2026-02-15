import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_market_data():
    """
        Consolidates raw scraped data into a clean master list.
        1. Removes items without prices.
        2. Filters out accessories (chargers, cases) and unrelated categories.
        3. Ensures the product is actually a percussive tool.
        """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    input_file = os.path.join(project_root, "data", "raw", "amazon_market_raw.jsonl")
    output_file = os.path.join(project_root, "data", "processed", "market_data_clean.jsonl")

    # Titles containing these are almost never the gun itself
    non_massager_list = [
        'charger', 'adapter', 'power cord', 'power supply', 'charging cable', 'replacement heads', 'mount', 'holder',
        'wall mount', 'extension handle', 'travel case', 'hard case', 'carrying case', 'vacuum gun', 'adjusting tool',
        'eye massager', 'heating pad', 'lacrosse ball', 'foot massager', 'scalp massager', 'duster', 'swiffer',
        'smart eye mask', 'weighted heating pad'
    ]

    # Titles must contain one of these to be considered hardware
    hardware_anchors = ['gun', 'massager', 'percussive', 'percussion', 'impact']

    clean_items = []
    total_processed = 0

    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            total_processed += 1
            item = json.loads(line)
            title = item.get('title', '').lower()
            price = item.get('price')

            # Gate 1: Price must exist (Removes discontinued/dead listings)
            if price is None or str(price).lower() == "none":
                continue

            # Gate 2: Remove known accessories and wrong categories
            if any(word in title for word in non_massager_list):
                continue

            # Gate 3: Must contain a hardware-specific keyword
            if not any(anchor in title for anchor in hardware_anchors):
                continue

            clean_items.append(item)

    # Save the consolidated list
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in clean_items:
            f.write(json.dumps(item) + '\n')

    logger.info(f"Purification Complete.")
    logger.info(f"Original Count: 252 | Purified Count: {len(clean_items)}")


if __name__ == "__main__":
    clean_market_data()