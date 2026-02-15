import json
import os

def augment_with_benchmarks():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    gold_path = os.path.join(project_root, "data", "processed", "gold_standards_cleaned.jsonl")
    market_path = os.path.join(project_root, "data", "processed", "market_data_clean.jsonl")
    output_path = os.path.join(project_root, "data", "processed", "final_augmented_market.jsonl")

    # These 5 brands are already in the scrape; we don't want to double-count them.
    existing_in_market = {
        "Theragun Elite",
        "Theragun Mini",
        "Hypervolt 2 Pro",
        "Lifepro Sonic",
        "Renpho Handheld"
    }

    injected_benchmarks = []
    with open(gold_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            # Normalize the name for the anchor search
            brand_model = item['brand_model']

            # Create a 'Rich Semantic' description
            # This makes the Gold Standard 'look' like an Amazon listing to SBERT
            synthetic_desc = (
                f"{brand_model} percussion massage gun. "
                f"Features {item['amplitude_mm']}mm amplitude for deep tissue therapy "
                f"and {item['stall_force_lbs']}lbs stall force. "
                f"Professional grade muscle recovery tool with {item['max_ppm']} PPM."
            )

            injected_benchmarks.append({
                "title": f"GOLD STANDARD: {item['brand_model']}",
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

    with open(market_path, 'r', encoding='utf-8') as f:
        market_items = [json.loads(line) for line in f]

    final_data = injected_benchmarks + market_items

    with open(output_path, 'w', encoding='utf-8') as f:
        for item in final_data:
            f.write(json.dumps(item) + '\n')

    print(f"Dataset ready. Injected {len(injected_benchmarks)} benchmarks into {len(market_items)} market items.")


if __name__ == "__main__":
    augment_with_benchmarks()