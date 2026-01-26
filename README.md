# Seattle Digital-to-Social Ratio (DSR) Analysis
**A Spatial Study of Infrastructure-Driven Behavioral Shifts**

## 🔬 Project Overview
This project investigates the relationship between residential internet reliability and public space behavior in Seattle. It tests the **"Connectivity Lifeboat"** theory: the hypothesis that lower home internet reliability forces residents to externalize digital activities into public spaces, thereby increasing the observed **Digital-to-Social Ratio (DSR)**.

### 🏛 Impact
This analysis provides a framework for the City of Seattle to identify **'Digital Refuges'**—public spaces that serve as critical infrastructure for neighborhoods with high socio-economic vulnerability.

### 🚀 Key Technical Findings
* **The Reliability Paradox:** Residential internet reliability was **not** a statistically significant predictor of public digital behavior (DSR) once socio-economic factors were controlled.
* **Socio-Economic Drivers:** Median household income and neighborhood demographics are the primary drivers. Higher-income ZIP codes exhibit significantly lower DSR ($p < 0.1$), suggesting wealthier areas lean toward social interaction over digital device usage in public.
* **Spatial Independence:** Global Moran’s I analysis of model residuals confirms spatial randomness ($p \approx 0.08$), indicating the model successfully accounts for geographic trends without systematic bias.
* **Model Volatility:** High Group Variance ($5.10$) in MixedLM indicates that public life is shaped by localized "Micro-Cultures" that resist city-wide generalizations.

---

## 🏗 Repository Structure
This project is modularized into a production-ready library and a nested analytical layer:

- `dsr_analysis/`: Core Python package.
    - `scripts/`: Production analytical pipeline (00-08).
    - `data_loader.py`: Specialized IO and cleaning logic.
    - `models.py`: Statistical engine implementing OLS, MixedLM (Random Intercepts), and GLM (Negative Binomial) specifications via statsmodels.
    - `spatial.py`: Geospatial transformations and WKT healing.
- `data/`: 
    - `raw/`: Source data (For details on origins/provenance, see [data:README.md](data:README.md)).
    - `processed/`: Standardized ABTs (Analytical Base Tables) and trimmed GeoJSON boundaries.
- `visualizations/`: Hierarchical storage of forest plots, marginal effects, and spatial heatmaps used in the final report.
- `reports/`: Contains `dsr_analysis_report.ipynb`, the primary executive document, extending from initial data audit to final conclusions.

---

## 🚀 Getting Started

### 1. Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```


### 2. Pipeline Execution
The analytical pipeline is located within dsr_analysis/scripts/. Run them in sequence to build the Analytical Base Table (ABT):

python dsr_analysis/scripts/00_data_audit.py: Validates file integrity.

python dsr_analysis/scripts/02_geojson_trimming.py: Standardizes spatial boundaries.

python dsr_analysis/scripts/04_clean_surveys.py: Harmonizes longitudinal survey data.

python dsr_analysis/scripts/05_create_master_table.py: Fuses equity and vitality metrics.

python dsr_analysis/scripts/06_model_visualizer.py: Generates regression forest plots.

### 3. Verify Code Integrity
```bash
pytest
```

## 📊 Methodology & Metrics
Target Variable (DSR): Calculated as the ratio of observed individuals using electronic devices vs. individuals engaged in social interaction:$$DSR = \frac{Digital}{Social + 1}$$

Statistical Rigor: All hypothesis testing is conducted with a significance threshold of $\alpha = 0.05$. While some variables (like Median Income) showed trends at the $p < 0.1$ level, they are interpreted with caution regarding city-wide generalizability.

Multi-Model Stack: Employs OLS for baseline, MixedLM to account for ZIP-level clustering, and Negative Binomial GLMs to validate count-based densities.

Causal Diagnostic: Employs a "Placebo Test" to ensure reliability predicts behavioral shifts (DSR) specifically, rather than general foot traffic volume.

## 🛠 Engineering & Statistics Stack
Modeling: statsmodels (OLS, MixedLM, GLM), patsy

Spatial: geopandas, libpysal, esda (Spatial Autocorrelation)

Visualization: matplotlib, seaborn

Infrastructure: pytest, logging, pathlib

## 📉 Limitations & Robustness
Sample Size & Granularity: Due to the municipal survey frequency ($N=32$ ZIP-Eras), results are exploratory and highlight the need for higher-granularity longitudinal data.

Self-Reporting Bias: The residential internet reliability metrics are derived from self-reported survey data. These may reflect perceived quality rather than technical throughput and are not strictly guaranteed to be a representative sample of the entire ZIP code population.

The "Commuter Assumption": A primary assumption of this study is that individuals observed in a specific ZIP code's public space also reside within that ZIP code. The data does not account for commuters or visitors who may live in areas with different infrastructure profiles than where they were observed.

The Income Gradient: The robust correlation between income and DSR suggests that "public digital life" is a proxy for broader socio-economic conditions rather than hardware access alone.


**Conclusion**: The "Connectivity Lifeboat" effect is highly localized. Public digital behavior in Seattle is a complex product of neighborhood identity and socio-economic status rather than a simple reaction to home outages.
