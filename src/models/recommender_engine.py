import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import os


def run_discovery_engine():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    vector_path = os.path.join(project_root, "data", "processed", "product_vectors.npy")
    meta_path = os.path.join(project_root, "data", "processed", "product_metadata.csv")

    vectors = np.load(vector_path)
    df = pd.read_csv(meta_path)

    # 1. Choose your Target (Anchor)
    # We'll search your 192 items for a 'Theragun Elite'
    target_keyword = "Theragun Elite"

    # Find the row in your 192 that most closely matches the Gold Standard title
    anchor_matches = df[df['title'].str.contains(target_keyword, case=False, na=False)]

    if anchor_matches.empty:
        # Fallback: if the exact item isn't in your 192, we'll pick the most expensive 'Theragun'
        anchor_matches = df[df['title'].str.contains("Theragun", case=False, na=False)].sort_values(by='price',
                                                                                                    ascending=False)

    if anchor_matches.empty:
        print(f"Could not find {target_keyword} in the 192 items.")
        return

    anchor_idx = anchor_matches.index[0]
    anchor_name = df.iloc[anchor_idx]['title']
    anchor_price = df.iloc[anchor_idx]['price']
    anchor_vector = vectors[anchor_idx].reshape(1, -1)

    print(f"🎯 BENCHMARK: {anchor_name} (${anchor_price})")

    # 2. Similarity Math
    similarities = cosine_similarity(anchor_vector, vectors).flatten()
    df['similarity'] = similarities

    # 3. Disruption Scoring
    # Logic: High similarity, Lower Price, High Rating
    df['price_ratio'] = df['price'] / anchor_price

    # We reward: High similarity (50%), Low price ratio (30%), High rating (20%)
    df['disruption_score'] = (
            (df['similarity'] * 0.5) +
            ((1 - df['price_ratio']) * 0.3) +
            ((df['average_rating'].fillna(0) / 5.0) * 0.2)
    )

    # 4. The "Anti-Clone" Filter
    # Filter out the anchor itself and items with zero reviews
    results = df[
        (df.index != anchor_idx) &
        (df['rating_number'] > 0) &
        (df['price'] < anchor_price)  # Must be cheaper to be a disruptor
        ].sort_values(by='disruption_score', ascending=False)

    print("\n--- TOP 3 STRATEGIC DISRUPTORS ---")
    for i, row in results.head(3).iterrows():
        print(f"🔥 {row['title'][:60]}...")
        print(f"   Similarity: {row['similarity']:.2f} | Price: ${row['price']:.2f} | Rating: {row['average_rating']}⭐")
        print(f"   Score: {row['disruption_score']:.3f}\n")


if __name__ == "__main__":
    run_discovery_engine()