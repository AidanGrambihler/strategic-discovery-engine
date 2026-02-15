import subprocess
import sys


def run_script(path):
    print(f"🚀 Running: {path}")
    result = subprocess.run([sys.executable, path], capture_output=False)
    if result.returncode != 0:
        print(f"❌ Error in {path}")
        sys.exit(1)


if __name__ == "__main__":
    # 1. Ingestion
    run_script("src/ingestion/scraper.py")
    run_script("src/ingestion/stream_market_data.py")

    # 2. Processing
    run_script("src/processing/process_gold_standards.py")
    run_script("src/processing/clean_market_data.py")
    run_script("src/processing/augment_data.py")

    # 3. Modeling
    run_script("src/models/product_embedder.py")
    run_script("src/models/recommender_engine.py")

    print("\n✅ Pipeline complete. Discovery Report generated.")