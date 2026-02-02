import json
import os


def augment_master_list():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    gold_path = os.path.join(project_root, "data", "processed", "gold_standards_cleaned.jsonl")
    master_path = os.path.join(project_root, "data", "processed", "amazon_massage_gun_master_v2.jsonl")
    output_path = os.path.join(project_root, "data", "processed", "amazon_massage_gun_augmented.jsonl")

    # 1. These 5 are already high-fidelity in our Amazon scrape
    # We do NOT want to inject 'GOLD STANDARD' versions of these.
    existing_anchors = {
        "Theragun Elite",
        "Theragun Mini",
        "Hypervolt 2 Pro",
        "Lifepro Sonic",
        "Renpho Handheld"
    }

    # 2. Load Gold Standards and Filter
    gold_to_inject = []
    with open(gold_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            brand_model = item['brand_model']

            # Logic: If it's one of the 5 we already have, skip the injection.
            if brand_model in existing_anchors:
                print(f"⏭️ Skipping {brand_model}: Using existing Amazon listing for anchor.")
                continue

            # Otherwise, format it for injection
            gold_to_inject.append({
                "title": f"GOLD STANDARD: {brand_model}",
                "price": item['price_usd'],
                "average_rating": 5.0,
                "rating_number": 1000,
                "features": [
                    f"Amplitude: {item['amplitude_mm']}mm",
                    f"Stall Force: {item['stall_force_lbs']}lbs",
                    f"Max PPM: {item['max_ppm']}"
                ],
                "store": "Official_Benchmark"
            })

    # 3. Load Amazon Master
    master_items = []
    with open(master_path, 'r', encoding='utf-8') as f:
        for line in f:
            master_items.append(json.loads(line))

    # 4. Combine and Save
    # We put the injected anchors first so they are easy to find in the CSV later
    final_list = gold_to_inject + master_items

    with open(output_path, 'w', encoding='utf-8') as f:
        for item in final_list:
            f.write(json.dumps(item) + '\n')

    print(f"\n✅ Created augmented list: {len(final_list)} total items.")
    print(f"🚀 Injected {len(gold_to_inject)} missing anchors.")
    print(f"🔗 Keeping 5 existing Amazon listings as native anchors.")


if __name__ == "__main__":
    augment_master_list()