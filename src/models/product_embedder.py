import json
import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_embeddings():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(base_dir, "../../")

    # Sync with new processing output
    input_file = os.path.join(project_root, "data", "processed", "final_augmented_market.jsonl")
    output_vectors = os.path.join(project_root, "data", "processed", "product_vectors.npy")
    output_metadata = os.path.join(project_root, "data", "processed", "product_metadata.csv")

    if not os.path.exists(input_file):
        logger.error(f"Source file not found: {input_file}")
        return

    items = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            items.append(json.loads(line))

    df = pd.DataFrame(items)

    # Concatenate title, features, and description for semantic search
    # Using fillna to ensure string concatenation doesn't fail on nulls
    titles = df['title'].fillna('')
    features = df['features'].apply(lambda x: " ".join(x) if isinstance(x, list) else "").fillna('')
    descriptions = df['description'].apply(lambda x: " ".join(x) if isinstance(x, list) else str(x) if pd.notnull(x) else "")
    df['combined_text'] = titles + " " + features + " " + descriptions

    # Load transformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    logger.info(f"Generating embeddings for {len(df)} products...")
    embeddings = model.encode(df['combined_text'].tolist(), show_progress_bar=True)

    # Save vectors and metadata separately
    np.save(output_vectors, embeddings)
    df.drop(columns=['combined_text']).to_csv(output_metadata, index=False)
    logger.info(f"Success! Saved {len(embeddings)} vectors.")

if __name__ == "__main__":
    generate_embeddings()