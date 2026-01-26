# Seattle Digital-to-Social Ratio (DSR) Analysis
**A Spatial Study of Infrastructure-Driven Behavioral Shifts**

## 🔬 Project Overview
This project investigates the relationship between residential internet reliability and public space behavior in Seattle. It tests the **"Connectivity Lifeboat"** theory: the hypothesis that lower home internet reliability forces residents to externalize digital activities into public spaces, thereby increasing the observed **Digital-to-Social Ratio (DSR)**.

### Key Technical Findings
* **The Reliability Paradox:** Contrary to the initial hypothesis, residential internet reliability was **not** a statistically significant predictor of public digital behavior (DSR) across OLS and Mixed-Effects models once socio-economic factors were controlled.
* **Socio-Economic Drivers:** Median household income and neighborhood demographics emerged as the primary drivers of public life. Higher-income ZIP codes exhibit significantly lower DSR ($p < 0.1$), suggesting that wealthier areas lean more toward social interaction over digital device usage in public.
* **Model Volatility:** Leave-One-Out (LOO) sensitivity analysis confirmed that digital behavior trends in Seattle are "brittle" and highly dependent on specific anchor neighborhoods rather than a uniform city-wide trend.
* **Spatial Independence:** Global Moran’s I analysis of model residuals confirms spatial randomness ($p \approx 0.08$), indicating the model successfully accounts for geographic trends without systematic bias.

## 🏗 Repository Structure (Shablona Standard)
Following scientific Python best practices, this project is modularized into a library and a narrative layer:

- `dsr_analysis/`: Core Python package containing data pipelines, regression logic, and spatial diagnostics.
- `scripts/`: Production-ready analytical scripts (e.g., `07_statistical_modelling.py`).
- `data/`: 
    - `raw/`: Original Seattle Open Data (Survey and Public Life observations).
    - `processed/`: `master_table.csv` (The Analytical Base Table).
- `visualizations/`: High-resolution forest plots, marginal effects charts, and spatial heatmaps.
- `tests/`: `pytest` suite ensuring data integrity and ZIP-code standardization.

---

## 🚀 Getting Started

### 1. Environment Setup
This project uses `pip` and `venv`. 
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

### 2. Run the Analysis
The primary statistical suite generates the multi-model comparison table and forest plots:
```bash
python scripts/07_statistical_modelling.py

### 3. Verify Code Integrity
To ensure the data pipeline and package paths are configured correctly, run the test suite:
```bash
pytest

## 📊 Methodology & Metrics
* **Target Variable (DSR):** Calculated as the ratio of observed individuals using electronic devices vs. individuals engaged in social interaction.
* **Multi-Model Stack:** Employs OLS for baseline, Mixed-Effects to account for ZIP-level clustering, and Negative Binomial GLMs to validate count-based user densities.
* **Causal Diagnostic (Placebo Test):** To ensure internal validity, the model tests if reliability predicts general foot traffic (Volume) versus behavioral shifts (DSR).



## 🛠 Tech Stack
* **Modeling:** `statsmodels` (OLS, MixedLM, GLM), `patsy`
* **Spatial:** `geopandas`, `libpysal`, `esda` (Moran's I)
* **Visuals:** `matplotlib`, `seaborn`

## 📉 Analytical Findings & Robustness
While initial hypotheses suggested a "Connectivity Lifeboat" effect, rigorous robustness testing revealed a more complex urban narrative:

* **Infrastructure vs. Culture:** Home internet reliability is a significant predictor of total foot traffic (Urban Vitality), but not the mode of activity (Digital vs. Social).
* **The Income Gradient:** As median income increases, DSR decreases—suggesting that "public digital life" is a proxy for broader socio-economic conditions rather than specific hardware access.
* **Neighborhood Variance:** A high Group Variance (5.10) in the MixedLM indicates that public life is shaped by highly localized "Micro-Cultures" that resist broad generalizations.



**Conclusion:** The "Connectivity Lifeboat" theory is not a city-wide rule in Seattle. Instead, public digital behavior is a complex product of neighborhood identity and socio-economic status.