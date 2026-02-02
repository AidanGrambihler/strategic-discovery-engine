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
    input_file = os.path.join(project_root, "data", "processed", "amazon_massage_gun_master.jsonl")
    output_vectors = os.path.join(project_root, "data", "processed", "product_vectors.npy")
    output_metadata = os.path.join(project_root, "data", "processed", "product_metadata.csv")

    # 2. Load the Master List
    items = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            items.append(json.loads(line))

    df = pd.DataFrame(items)
    logger.info(f"Loaded {len(df)} products for embedding.")

    # 3. Create "Rich Text" for the Model
    # We combine title and features to give the model maximum context
    df['combined_text'] = df['title'] + " " + df['features'].apply(lambda x: " ".join(x) if isinstance(x, list) else "")

    # 4. Initialize SBERT (PyTorch)
    # 'all-MiniLM-L6-v2' is the industry standard for speed/accuracy balance
    model = SentenceTransformer('all-MiniLM-L6-v2')

    logger.info("Encoding products... (This may take a minute on CPU)")
    embeddings = model.encode(df['combined_text'].tolist(), show_progress_bar=True)

    # 5. Save the results
    # We save vectors as .npy for fast loading and metadata as .csv for easy lookup
    np.save(output_vectors, embeddings)
    df.drop(columns=['combined_text']).to_csv(output_metadata, index=False)

    logger.info(f"Success! Vectors saved to {output_vectors}")


if __name__ == "__main__":
    generate_embeddings()