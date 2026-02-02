import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import os


def run_professional_discovery():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    vector_path = os.path.join(project_root, "data", "processed", "product_vectors.npy")
    meta_path = os.path.join(project_root, "data", "processed", "product_metadata.csv")

    vectors = np.load(vector_path)
    df = pd.read_csv(meta_path)

    # Your 11 Gold Standards
    gold_standards = [
        "Theragun Pro", "Theragun Elite", "Theragun Mini",
        "Hypervolt 2 Pro", "Ekrin Athletics Bantam", "Theragun Prime",
        "Bob and Brad Q2", "Lifepro Sonic", "Ekrin Athletics B37",
        "Mighty Bliss", "Renpho Handheld"
    ]

    print(f"--- STRATEGIC DISCOVERY REPORT: 11 ANCHORS VS {len(df)} PRODUCTS ---")

    for target in gold_standards:
        # 1. Find the Anchor in your data
        matches = df[df['title'].str.contains(target, case=False, na=False)]
        if matches.empty:
            continue

        anchor_idx = matches.index[0]
        anchor_vector = vectors[anchor_idx].reshape(1, -1)
        anchor_price = df.iloc[anchor_idx]['price']

        # 2. Math & Scoring
        df['similarity'] = cosine_similarity(anchor_vector, vectors).flatten()
        df['price_ratio'] = df['price'] / anchor_price
        df['confidence_modifier'] = df['rating_number'].apply(lambda x: min(x / 50, 1.0))

        # Weighted Disruption Score
        df['disruption_score'] = (
                (df['similarity'] * 0.60) +
                ((1 - df['price_ratio']) * 0.25) +
                ((df['average_rating'].fillna(0) / 5.0) * df['confidence_modifier'] * 0.15)
        )

        # 3. Filter for quality
        disruptors = df[
            (df.index != anchor_idx) &
            (df['similarity'] > 0.65) &  # Must be a decent match
            (df['price'] >= 35.0) &  # Filter out the 'vibrating toy' tier
            (df['price'] < anchor_price)  # Must actually be a deal
            ].sort_values(by='disruption_score', ascending=False)

        # 4. Print results
        print(f"\n🔎 ANCHOR: {target} (${anchor_price})")
        if not disruptors.empty:
            top = disruptors.iloc[0]
            print(f"   🏆 TOP DISRUPTOR: {top['title'][:55]}...")
            print(f"   📊 Score: {top['disruption_score']:.3f} | Sim: {top['similarity']:.2f} | Price: ${top['price']}")
        else:
            print("   ❌ No high-quality disruptors found.")


if __name__ == "__main__":
    run_professional_discovery()