import json
import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_embeddings():
    # 1. Path Setup
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    input_file = os.path.join(project_root, "data", "processed", "amazon_massage_gun_master_v2.jsonl")
    output_vectors = os.path.join(project_root, "data", "processed", "product_vectors.npy")
    output_metadata = os.path.join(project_root, "data", "processed", "product_metadata.csv")

    # 2. Load Data
    items = []
    if not os.path.exists(input_file):
        logger.error(f"Input file not found at {input_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            items.append(json.loads(line))

    df = pd.DataFrame(items)
    logger.info(f"Loaded {len(df)} products for embedding.")

    # 3. Feature Engineering: Create "Rich Text"
    # We combine title and features so the model understands the technical context
    df['combined_text'] = df['title'] + " " + df['features'].apply(lambda x: " ".join(x) if isinstance(x, list) else "")

    # 4. Model Initialization (SBERT)
    model = SentenceTransformer('all-MiniLM-L6-v2')

    logger.info("Encoding products to vector space...")
    embeddings = model.encode(df['combined_text'].tolist(), show_progress_bar=True)

    # 5. Persistence
    np.save(output_vectors, embeddings)
    # Drop the heavy text column before saving the metadata CSV
    df.drop(columns=['combined_text']).to_csv(output_metadata, index=False)

    logger.info(f"Success! Saved {len(embeddings)} vectors.")

if __name__ == "__main__":
    generate_embeddings()