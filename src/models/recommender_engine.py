import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import os

def run_discovery_engine():
    # 1. Path Setup
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    vector_path = os.path.join(project_root, "data", "processed", "product_vectors.npy")
    meta_path = os.path.join(project_root, "data", "processed", "product_metadata.csv")

    if not os.path.exists(vector_path) or not os.path.exists(meta_path):
        print("Error: Missing data files. Run product_embedder.py first.")
        return

    vectors = np.load(vector_path)
    df = pd.read_csv(meta_path)

    # 2. HYBRID MAPPING: Scraped + Injected Gold Standards
    # We use specific Amazon fragments for the 5 found in the scrape
    # We use the "GOLD STANDARD" prefix for the 6 we injected
    anchor_map = {
        "Theragun Elite": "TheraGun Elite",
        "Theragun Mini": "Theragun G3",
        "Hypervolt 2 Pro": "Hypervolt 2 Pro",
        "Lifepro Sonic": "LifePro Mini",
        "Renpho Handheld": "RENPHO Active",

        "Theragun Pro": "GOLD STANDARD: Theragun Pro",
        "Ekrin Bantam": "GOLD STANDARD: Ekrin Athletics Bantam",
        "Theragun Prime": "GOLD STANDARD: Theragun Prime",
        "Bob and Brad Q2": "GOLD STANDARD: Bob and Brad Q2",
        "Ekrin B37": "GOLD STANDARD: Ekrin Athletics B37",
        "Mighty Bliss": "GOLD STANDARD: Mighty Bliss"
    }

    print(f"--- MASSAGE GUN DISRUPTION REPORT ({len(anchor_map)} ANCHORS) ---\n")

    for spec_name, search_term in anchor_map.items():
        # Find the specific row for our Anchor
        matches = df[df['title'].str.contains(search_term, case=False, na=False)]
        if matches.empty:
            continue

        anchor_idx = matches.index[0]
        anchor_vector = vectors[anchor_idx].reshape(1, -1)
        anchor_price = df.iloc[anchor_idx]['price']

        # 3. Scoring Math
        df['similarity'] = cosine_similarity(anchor_vector, vectors).flatten()
        df['price_ratio'] = df['price'] / anchor_price
        df['conf_mod'] = df['rating_number'].apply(lambda x: min(x / 50, 1.0))

        # Weighted Disruption Score
        df['disruption_score'] = (
                (df['similarity'] * 0.60) +
                ((1 - df['price_ratio']) * 0.25) +
                ((df['average_rating'].fillna(0) / 5.0) * df['conf_mod'] * 0.15)
        )

        # 4. Filter for legitimate "Market" Disruptors
        # CRITICAL FIX: Exclude the anchor AND any title containing 'GOLD STANDARD'
        # This ensures we only find market clones, not our own benchmarks.
        disruptors = df[
            (df.index != anchor_idx) &
            (~df['title'].str.contains("GOLD STANDARD", case=False, na=False)) &
            (df['similarity'] > 0.65) &
            (df['price'] < (anchor_price * 0.8)) & # At least 20% cheaper
            (df['price'] >= 35.0)                  # Quality floor
        ].sort_values(by='disruption_score', ascending=False)

        # 5. Output Results
        print(f"🎯 TARGET ANCHOR: {spec_name} (${anchor_price:.2f})")
        if not disruptors.empty:
            top = disruptors.iloc[0]
            savings = (1 - top['price_ratio']) * 100
            print(f"   🔥 DISRUPTOR: {top['title'][:60]}...")
            print(f"   📊 Score: {top['disruption_score']:.3f} | Sim: {top['similarity']:.2f} | Price: ${top['price']} ({savings:.0f}% savings)")
        else:
            print("   ❌ No high-value market disruptors found.")
        print("-" * 65)

if __name__ == "__main__":
    run_discovery_engine()