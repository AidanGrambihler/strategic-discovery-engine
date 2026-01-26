# Data Registry & Technical Schema

This directory manages the raw source files and the transformation logic used to build the final analytical base table (ABT). All municipal data was retrieved from the [Seattle Open Data Portal](https://data.seattle.gov/) on **January 22, 2026**.

## 🔄 Data Lineage & Pipeline
The project follows a linear transformation pipeline to ensure reproducibility:
1. **Raw Layer (`/data/raw`):** Immutable source files from Seattle Open Data.
2. **Feature Engineering (`scripts/03_feature_engineering.py`):** Normalization of income buckets and calculation of the DSR ratio.
3. **Analytical Base Table (`/data/processed/master_table.csv`):** The final joined, Z-scored, and pruned dataset used in the model stack.

---

## 🏗️ Anchor Data: Public Life (SDOT)
*Agency: Seattle Department of Transportation (SDOT)*

| Local Filename | Official Dataset Name | Key Function | Raw Columns Used |
| :--- | :--- | :--- | :--- |
| `locations.csv` | [Public Life - Locations](https://data.seattle.gov/...) | Block-level IDs | `Location ID`, `Neighborhood` |
| `staying.csv` | [Public Life - Staying](https://data.seattle.gov/...) | **Dependent Variable** | `Electronic Communication`, `Social Communication` |
| `geography.csv` | [Public Life - Geography](https://data.seattle.gov/...) | GIS Geometries | `geometry`, `Location ID` |

### ⚠️ Methodological Pruning: `moving.csv`
`moving.csv` (pedestrian flow) was excluded from the final regression stack. 
* **Reason:** It lacked behavioral markers (electronic device usage) required for DSR calculation. 
* **Impact:** Focuses the model on "dwell time" behavior where digital vs. social choice is most deliberate.

---

## 🌐 Supplemental Data: Digital Equity (IT)
*Agency: Seattle Information Technology - Digital Equity Team*

| Local Filename | Official Dataset Name | Key Function | N (Original) |
| :--- | :--- | :--- | :--- |
| `tech_survey_2018.csv` | [Technology Access 2018](https://data.seattle.gov/...) | Baseline Metrics | 4,315 |
| `tech_survey_2023.csv` | [Technology Access 2023](https://data.seattle.gov/...) | Modern Metrics | 2,780 |

---

## 🛠️ Field Mappings & Standardization

### 1. The Digital-to-Social Ratio (DSR)
The DSR is the core behavioral metric. It is calculated as:
$$DSR = \frac{\text{Electronic Communication}}{\text{Social Communication} + 1}$$
*(The $+1$ Laplace smoothing is applied to prevent division-by-zero errors in social-heavy ZIP codes.)*

### 2. Inflation-Adjusted Income Normalization
Income was binned into a 1–7 index to maintain longitudinal validity across a ~21.2% CPI-U shift (2018–2023).

| Unified Index | 2018 Nominal Range | 2023 Survey Range |
| :---: | :--- | :--- |
| **1** | Below $25k | Less than $27k |
| **4** | $75k - $100k | $75k - $100k |
| **7** | $200k+ | $200k+ |

---

## ⚖️ Methodological Rigor

### 📍 The Locality Assumption
Consistent with urban planning standards (e.g., Gehl Institute), we assume users in neighborhood plazas are residents of that specific ZIP code. This allows us to use residential survey data as environmental predictors of plaza behavior.

### 🔢 The "Small N" Rule ($N \ge 50$)
Per Seattle IT data privacy guidelines, ZIP-level survey results were only included if they contained $\ge 50$ responses. 
* **Result:** Pruned 4 ZIP codes from the final model to prevent outlier-driven bias.

### 🗓️ Temporal Lumping (Era Proxies)
To maximize statistical power ($N=32$ final modeling units), observations are aggregated into:
* **Pre-Pandemic ('2018'):** 2018–2019 survey & observation data.
* **Post-Pandemic ('2023'):** 2022–2023 survey & observation data.