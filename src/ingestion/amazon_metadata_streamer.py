import json
from datasets import load_dataset


def stream_and_filter_recovery_data(output_path):
    # 1. Define your "Recovery DNA" keywords
    keywords = ["massage gun", "percussive", "foam roller", "compression boots", "muscle recovery"]
    count = 0

    print("Connecting to McAuley Lab faucet... this may take a moment.")

    # 2. Open the 'faucet' (streaming=True)
    dataset = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        "raw_meta_Health_and_Household",
        split="full",
        streaming=True,
        trust_remote_code=True
    )

    # 3. Process and Save on-the-fly
    with open(output_path, 'w') as f:
        for item in dataset:
            # Combine title and features for a robust search
            title = item.get('title', '') or ''
            features = " ".join(item.get('features', []) or [])
            text_to_check = (title + " " + features).lower()

            if any(kw in text_to_check for kw in keywords):
                f.write(json.dumps(item) + '\n')
                count += 1

                # Progress update every 100 items so you don't feel stuck
                if count % 100 == 0:
                    print(f"Found {count} products so far...")

    print(f"Done! Saved {count} recovery products to {output_path}")

# Run this Sunday morning!
# stream_and_filter_recovery_data('data/processed/amazon_recovery_items.jsonl')