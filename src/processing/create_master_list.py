import json
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_master_list():
    # 1. Setup Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../../"))

    input_file = os.path.join(project_root, "data", "processed", "amazon_hardware_refined.jsonl")
    output_file = os.path.join(project_root, "data", "processed", "amazon_massage_gun_master.jsonl")

    if not os.path.exists(input_file):
        logger.error(f"Source file not found: {input_file}")
        return

    processed_count = 0
    saved_count = 0

    logger.info("Starting Master List generation (Purging null prices)...")

    # 2. Process and Filter
    with open(input_file, 'r', encoding='utf-8') as infile, \
            open(output_file, 'w', encoding='utf-8') as outfile:

        for line in infile:
            processed_count += 1
            try:
                item = json.loads(line)

                # The Golden Rule: Price must exist and not be None
                price = item.get("price")

                if price is not None and str(price).lower() != "none":
                    outfile.write(json.dumps(item) + '\n')
                    saved_count += 1
            except json.JSONDecodeError:
                continue

    logger.info(f"Done! Processed: {processed_count:,} | Saved to Master: {saved_count:,}")
    logger.info(f"Master List location: {output_file}")


if __name__ == "__main__":
    generate_master_list()