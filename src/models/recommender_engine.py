import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import os

def run_discovery_engine():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(base_dir, "../../")

    vector_path = os.path.join(project_root, "data", "processed", "product_vectors.npy")
    meta_path = os.path.join(project_root, "data", "processed", "product_metadata.csv")

    if not os.path.exists(vector_path):
        print("Vectors not found. Run product_embedder.py first.")
        return

    vectors = np.load(vector_path)
    df = pd.read_csv(meta_path)

    # Mapping market leaders to their search terms in the dataset
    anchor_map = {
        # 1. Native Amazon Anchors (Flexible partial matches)
        "Theragun Elite": "Theragun Elite",
        "Theragun Mini": "Theragun Mini",
        "Hypervolt 2 Pro": "Hypervolt 2 Pro",
        "Lifepro Sonic": "LifePro Sonic",
        "Renpho Active": "RENPHO Active",

        # 2. Injected Gold Standards (Exact matches from augment_data.py)
        "Theragun Pro": "GOLD STANDARD: Theragun Pro Plus G6",
        "Ekrin Bantam": "GOLD STANDARD: Ekrin Athletics Bantam",
        "Theragun Prime": "GOLD STANDARD: Theragun Prime",
        "Bob and Brad Q2": "GOLD STANDARD: Bob and Brad Q2 Mini",
        "Ekrin B37": "GOLD STANDARD: Ekrin Athletics B37",
        "Mighty Bliss": "GOLD STANDARD: Mighty Bliss Cordless",
        #"Renpho Active": "GOLD STANDARD: Renpho Handheld"
    }

    print("--- MARKET DISRUPTION REPORT ---\n")

    for display_name, search_term in anchor_map.items():
        # Find the anchor row
        match = df[df['title'].str.contains(search_term, case=False, na=False)]
        if match.empty:
            continue

        idx = match.index[0]
        anchor_vec = vectors[idx].reshape(1, -1)
        anchor_price = df.iloc[idx]['price']

        # Math: 60% Semantic Similarity, 25% Price Savings, 15% Verified Rating Quality
        df['similarity'] = cosine_similarity(anchor_vec, vectors).flatten()
        df['price_ratio'] = df['price'] / anchor_price

        # Scaling rating count to prevent 1-review products from skewing results
        df['trust_mod'] = df['rating_number'].apply(lambda x: min(x / 50, 1.0))

        # If similarity is under 0.65, we heavily penalize the score
        df['sim_penalty'] = df['similarity'].apply(lambda x: 1.0 if x > 0.65 else 0.5)

        df['disruption_score'] = (
            (df['similarity'] * 0.50) +  # Weigh similarity higher
            ((1 - df['price_ratio']) * 0.30) +  # Weigh savings slightly lower
            ((df['average_rating'].fillna(0) / 5.0) * df['trust_mod'] * 0.20)
        ) * df['sim_penalty']

        # Filter for candidates: >20% price drop, high similarity, excluding benchmarks
        disruptors = df[
            (df.index != idx) &
            (~df['title'].str.contains("GOLD STANDARD", case=False, na=False)) &
            (df['similarity'] > 0.60) &
            (df['price'] < (anchor_price * 0.9)) &
            (df['price'] >= 30.0)
            ].sort_values(by='disruption_score', ascending=False)

        print(f"TARGET ANCHOR: {display_name} (${anchor_price:.2f})")
        if not disruptors.empty:
            top = disruptors.iloc[0]
            savings = (1 - top['price_ratio']) * 100
            print(f" > BEST ALTERNATIVE: {top['title'][:55]}...")
            print(
                f" > Score: {top['disruption_score']:.3f} | Sim: {top['similarity']:.2f} | Price: ${top['price']} ({savings:.0f}% off)")
        else:
            print(" > No significant market disruptors found.")
        print("-" * 65)

if __name__ == "__main__":
    run_discovery_engine()