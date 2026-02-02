import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import os


def run_final_discovery():
    # 1. Path Setup
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    vector_path = os.path.join(project_root, "data", "processed", "product_vectors.npy")
    meta_path = os.path.join(project_root, "data", "processed", "product_metadata.csv")

    if not os.path.exists(vector_path) or not os.path.exists(meta_path):
        print("Error: Missing data files. Run product_embedder.py first.")
        return

    vectors = np.load(vector_path)
    df = pd.read_csv(meta_path)

    # 2. MAPPING: Spec Name -> Amazon Title Fragment
    # This aligns your 11 Gold Standards with the actual strings found in your 192 list
    anchor_map = {
        "Theragun Elite": "TheraGun Elite",
        "Theragun Mini": "Theragun G3",  # Using G3 as the small-frame proxy
        "Hypervolt 2 Pro": "Hypervolt 2 Pro",
        "Hypervolt 2": "Hypervolt 2 - Featuring",
        "Lifepro Sonic": "LifePro Mini",
        "Renpho Active": "RENPHO Active",
    }

    print(f"--- STRATEGIC DISRUPTION REPORT: {len(anchor_map)} ANCHORS ---\n")

    for spec_name, amazon_fragment in anchor_map.items():
        # Identify Anchor Row
        matches = df[df['title'].str.contains(amazon_fragment, case=False, na=False)]
        if matches.empty:
            continue

        anchor_idx = matches.index[0]
        anchor_vector = vectors[anchor_idx].reshape(1, -1)
        anchor_price = df.iloc[anchor_idx]['price']

        # 3. Calculation Logic
        # Calculate Cosine Similarity against all 192 items
        df['similarity'] = cosine_similarity(anchor_vector, vectors).flatten()

        # Price Ratio: Percentage of anchor price (Lower is better for a disruptor)
        df['price_ratio'] = df['price'] / anchor_price

        # Confidence: Penalty for items with < 50 reviews (Market Proof)
        df['confidence'] = df['rating_number'].apply(lambda x: min(x / 50, 1.0))

        # Weighted Score (60% Tech Similarity, 25% Price Value, 15% Market Trust)
        df['disruption_score'] = (
                (df['similarity'] * 0.60) +
                ((1 - df['price_ratio']) * 0.25) +
                ((df['average_rating'].fillna(0) / 5.0) * df['confidence'] * 0.15)
        )

        # 4. Filter for legitimate Disruptors
        # Must be at least 20% cheaper and have a similarity floor of 0.65
        disruptors = df[
            (df.index != anchor_idx) &
            (df['similarity'] > 0.65) &
            (df['price'] < (anchor_price * 0.8)) &
            (df['price'] >= 35.0)  # Quality floor
            ].sort_values(by='disruption_score', ascending=False)

        print(f"🎯 TARGET ANCHOR: {spec_name} (${anchor_price:.2f})")
        if not disruptors.empty:
            top = disruptors.iloc[0]
            savings = (1 - top['price_ratio']) * 100
            print(f"   🔥 DISRUPTOR: {top['title'][:60]}...")
            print(
                f"   📊 Score: {top['disruption_score']:.3f} | Sim: {top['similarity']:.2f} | Price: ${top['price']} ({savings:.0f}% savings)")
        else:
            print("   ❌ No high-value disruptors found meeting the quality threshold.")
        print("-" * 60)


if __name__ == "__main__":
    run_final_discovery()