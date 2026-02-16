# Amazon Hardware Arbitrage: NLP-Driven Market Disruption
**Quantifying Technical Clones and Price Inefficiencies in Percussive Therapy Markets**

## 🔬 Project Overview
This project identifies **"Market Disruptors"**—products that are technically and semantically near-identical to high-end industry benchmarks (e.g., Theragun, Hyperice) but retail at a fraction of the cost. Using **SBERT (Sentence-BERT)** embeddings and custom **Disruption Scoring**, the engine maps the "Semantic DNA" of 200+ hardware products to find arbitrage opportunities for consumers.

### 🏛 Impact
This tool transforms unstructured e-commerce data into a **Strategic Decision Engine**. It allows users to bypass "Brand Premiums" by mathematically identifying the technical floor of a product's hardware specifications.

### 🚀 Key Technical Findings
* **The "True Clone" Discovery:** The engine identified a 0.87 semantic match for the Renpho Active, pointing to a handheld massager at 44% savings. In NLP terms, a similarity > 0.85 indicates near-identical technical descriptions and hardware use-cases.

* **The Budget Frontier:** For premium anchors like the Theragun Elite ($389), the engine identified "Aggressive Disruptors" like the ORIbox, offering 91% price reductions. While the similarity (0.61) suggests a generic hardware profile, the disruption score highlights a massive arbitrage opportunity for non-professional users.

* **Form-Factor Intelligence:** The model successfully distinguished between device sizes, correctly matching the Theragun Mini with a specialized Portable Mini Massage Gun (0.62 similarity) rather than full-sized alternatives.

* **The Professional Moat:** The Ekrin Bantam remains a "Market Outlier." No products in the current dataset met the 0.60 similarity and price-drop criteria simultaneously, validating Ekrin’s unique market positioning in the sub-$200 professional tier.

---

## 🏗 Repository Structure
The project is architected for modularity, separating the Extraction, Transformation, and Inference layers:

- `src/`: Core project logic.
    - `ingestion/`: Scripts for raw data acquisition (`scraper.py`, `stream_market_data.py`)
    - `processing/`: Data cleaning and benchmarking logic (`clean_market_data.py`, `process_gold_standards.py`, `augment_data.py`)
    - `models/`: NLP inference and discovery logic (`product_embedder.py`, `recommender_engine.py`)
- `data/`: Storage for all stateful data.
    - `raw/`: Unmodified source files (`amazon_market_raw.jsonl`, `gold_standards.jsonl`)
    - `processed/`: Cleaned ABTs and serialized NLP artifacts (`product_vectors.npy`, `product_metadata.csv`)
- `notebooks/`: 
    - `eda.ipynb`: Visualizing the "Arbitrage Frontier" and auditing market integrity.
- `run_pipeline.py`: The orchestration script that executes the end-to-end pipeline in sequence.
- `requirements.txt`: Defined dependencies for environment reproducibility.

---
## 🚀 Getting Started

### 1. Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
```

### 2. Full Pipeline Execution
The entire discovery engine, from raw data ingestion to NLP vectorization, is orchestrated via a single entry point. This ensures data consistency across the processing layers.

```bash
python run_pipeline.py
```

### 3. Modular Execution
If you wish to run specific stages of the pipeline independently, you can call the sub-modules directly:

* Ingestion: `python src/ingestion/scraper.py`
* Refinement: `python src/processing/augment_data.py`
* Inference: `python src/models/recommender_engine.py`

## 📊 Methodology & Metrics

**Disruption Score ($DS$)**: A weighted multi-objective function designed to balance technical similarity, financial incentive, and market trust. This ensures the model recommends viable products rather than just the cheapest possible items.

$$DS = (Sim \times 0.40) + ((1 - \frac{P_{disruptor}}{P_{anchor}}) \times 0.40) + (Trust_{mod} \times 0.20)$$

* **Semantic Similarity ($Sim$)**: Captured via Cosine Similarity of SBERT embeddings. With a Hard Floor of 0.60, any product below this is rejected as "Categorically Dissimilar."
* **Price Incentive**: A linear measure of savings. This project defines "Disruption" as a minimum 15% price reduction relative to the anchor.
* **Trust Modifier ($Trust_{mod}$)**: A confidence-weighted rating score. It scales the `average_rating` by the `rating_number` to penalize products with high ratings but low review counts (unverified quality).

**Data Augmentation**: To account for gaps in the 2023 Amazon dataset (which lacked several modern market leaders), the model performs a **Reference Injection**. It maps 11 "Gold Standard" products with verified physical specifications (Stall Force, Amplitude) into the vector space. This creates a high-fidelity "North Star" for the discovery engine to benchmark against messy, scraped market data.

---

## 🛠 Engineering & ML Stack

* **Modeling & NLP**: `sentence-transformers` (PyTorch implementation of SBERT), `scikit-learn` (Efficient Cosine Similarity computation).
* **Data Orchestration**: `pandas` and `numpy` for matrix operations; `duckdb` for high-performance SQL audits and data integrity checks.
* **Visualization**: `matplotlib` and `seaborn` for mapping the Price-Similarity Arbitrage Frontier.
* **Infrastructure**: Modular Python scripts organized for reproducibility and pipeline automation.

---

## 📉 Limitations & Robustness

* **The Semantic Proxy**: This model assumes that Amazon titles and feature lists are accurate proxies for internal hardware. While semantic similarity is a strong indicator of "Cloning," it does not replace a physical teardown or electrical testing.
* **Temporal Variance**: Price ratios are calculated based on the dataset's snapshot; real-time Amazon price fluctuations (coupons, lightning deals) are not accounted for in this static version.
* **The "Cheap-Bias" Effect**: With a $0.40$ weight on price savings, the engine currently favors extreme budget options ($30-$50). Future iterations could implement Price Tiering to find "Pro-Summers" (e.g., $150 alternatives for $600 anchors).
* **Feature Sparsity**: The current model relies heavily on Title and Store metadata. Adding `stall_force_lbs` and `amplitude_mm` directly into the vector space would further sharpen the "Hardware DNA" matching.

**Conclusion**: This project demonstrates that NLP can effectively "look through" luxury branding to find technical equivalents. By quantifying the relationship between price and semantic DNA, we prove that for 80% of the massage gun market, consumers are paying for a logo, not a motor.