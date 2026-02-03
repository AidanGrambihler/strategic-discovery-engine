# Amazon Hardware Arbitrage: NLP-Driven Market Disruption
**Quantifying Technical Clones and Price Inefficiencies in Percussive Therapy Markets**

## 🔬 Project Overview
This project identifies **"Market Disruptors"**—products that are technically and semantically near-identical to high-end industry benchmarks (e.g., Theragun, Hyperice) but retail at a fraction of the cost. Using **SBERT (Sentence-BERT)** embeddings and custom **Disruption Scoring**, the engine maps the "Semantic DNA" of 200+ hardware products to find arbitrage opportunities for consumers.

### 🏛 Impact
This tool transforms unstructured e-commerce data into a **Strategic Decision Engine**. It allows users to bypass "Brand Premiums" by mathematically identifying the technical floor of a product's hardware specifications.

### 🚀 Key Technical Findings
* **The High-End Moat:** Professional-grade anchors (e.g., Theragun Pro at $650) exhibit high "Technical Uniqueness." Within the current market scrape, 0 products met the disruption criteria for the Pro tier, suggesting a hardware specification gap that generic manufacturers have yet to bridge.
* **Entry-Level Saturation:** Entry-level anchors (e.g., Renpho, Lifepro) show high "Clone Density," with disruptors offering up to **53% savings** at a **0.87 semantic similarity**, indicating these products are functionally interchangeable.
* **Successful Arbitrage:** The **Wattne Massage Gun** was identified as the primary disruptor for the **Theragun Elite**, offering an **86% price reduction** ($59.99 vs $423.00) while maintaining a significant semantic overlap (0.66).

---

## 🏗 Repository Structure
The project is architected to separate raw web-scraped data from validated industry benchmarks:

- `src/`: Core Python logic.
    - `data/processing/augment_data.py`: A data-fusion script that injects "Gold Standard" benchmarks into the scraped dataset using conditional de-duplication.
    - `models/product_embedder.py`: PyTorch-based inference engine using `all-MiniLM-L6-v2` to vectorize product titles and features.
    - `models/recommender_engine.py`: The logic layer that calculates Disruption Scores and filters market results.
- `data/`: 
    - `raw/`: Original McAuley Lab Amazon dataset and manual `gold_standards.jsonl`.
    - `processed/`: Augmented Analytical Base Tables (ABT) and saved `.npy` vector embeddings.
- `notebooks/`: 
    - `01_amazon_market_inventory_eda.ipynb`: Market integrity audits and Price-vs-Similarity frontier visualizations.
    - `02_amazon_behavior_analysis.ipynb`: Analysis of rating trust and review-count confidence.

---

## 🚀 Getting Started

### 1. Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

### 2. Pipeline Execution
Run the pipeline to generate the vector space and discovery report:

Augment Data: python src/data/processing/augment_data.py (Fuses benchmarks with market data).

Generate Embeddings: python src/models/product_embedder.py (Creates the vector space).

Run Discovery: python src/models/recommender_engine.py (Outputs the Disruption Report).

## 📊 Methodology & Metrics

**Disruption Score ($DS$)**: A weighted multi-objective function designed to balance technical similarity, financial incentive, and market trust. This ensures the model recommends viable products rather than just the cheapest possible items.

$$DS = (Sim \times 0.60) + ((1 - \frac{P_{disruptor}}{P_{anchor}}) \times 0.25) + (Trust_{mod} \times 0.15)$$

* **Semantic Similarity ($Sim$)**: Calculated using Cosine Similarity between SBERT embedding vectors. This captures the "Technical DNA" of the product beyond simple keyword matching.
* **Price Ratio**: Measures the financial incentive. A higher weight is given to products that offer significant savings over the luxury anchor.
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
* **Market Coverage**: The "No Disruptors Found" results for the Professional tier (e.g., Theragun Pro) likely reflect the current 200-item sample size. Expanding the scrape to 10k+ items would likely reveal specialized boutique competitors.

**Conclusion**: This project demonstrates that NLP can effectively "look through" luxury branding to find technical equivalents. By quantifying the relationship between price and semantic DNA, we prove that for 80% of the massage gun market, consumers are paying for a logo, not a motor.