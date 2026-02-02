import pandas as pd
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def purify_to_hardware_only():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    input_file = os.path.join(project_root, "data", "processed", "amazon_massage_gun_master.jsonl")
    output_file = os.path.join(project_root, "data", "processed", "amazon_massage_gun_master_v2.jsonl")

    # 1. THE "Killed by Association" List
    # Items containing these are almost never the gun itself
    accessory_blacklist = [
        'charger', 'adapter', 'power cord', 'power supply', 'charging cable',
        'replacement heads', 'mount', 'holder', 'wall mount', 'extension handle',
        'travel case', 'hard case', 'carrying case', 'vacuum gun', 'adjusting tool'
    ]

    # 2. THE "Wrong Category" List
    # Items that are massagers but NOT the hardware guns we want
    non_gun_massagers = [
        'eye massager', 'heating pad', 'lacrosse ball', 'foot massager',
        'scalp massager', 'duster', 'swiffer', 'smart eye mask', 'weighted heating pad'
    ]

    clean_items = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            title = item.get('title', '').lower()

            # GATE 1: Check Blacklists
            if any(word in title for word in accessory_blacklist):
                continue
            if any(word in title for word in non_gun_massagers):
                continue

            # GATE 2: Must contain a "Hardware Anchor"
            # This ensures we don't accidentally keep a random "Therapy" book or something
            hardware_anchors = ['gun', 'massager', 'percussive', 'percussion', 'impact']
            if not any(anchor in title for anchor in hardware_anchors):
                continue

            clean_items.append(item)

    # Save the purified list
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in clean_items:
            f.write(json.dumps(item) + '\n')

    logger.info(f"Purification Complete.")
    logger.info(f"Original Count: 252 | Purified Count: {len(clean_items)}")


if __name__ == "__main__":
    purify_to_hardware_only()