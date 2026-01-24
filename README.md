Seattle Urban Vitality & Digital Equity Index
An analysis of physical public life and digital infrastructure reliance.

📌 Project Overview
This project investigates the relationship between neighborhood-level digital access and the actual observed behavior of people in public spaces. By anchoring 2023 SDOT Public Life observation data with the Technology Access and Adoption Survey, we aim to identify if public spaces serve as "critical digital hubs" in neighborhoods with low home-broadband adoption.

🎯 Primary Research Question
Does lower residential internet reliability predict higher digital activity in public spaces, independent of neighborhood income—and has this relationship intensified post-pandemic?

💡 Hypotheses
H1 (Substitution): Lower home reliability correlates with higher public Digital-to-Social Ratios (DSR).

H2 (Independence): This effect persists even when controlling for median income.

H3 (Intensity): The "Reliability Gap" in public behavior is wider in 2023 than in 2018.

📊 The Data
Anchor: Seattle Public Life Data (Observations of people staying, moving, and using electronics).

Supplement: Technology Access and Adoption Survey (300+ variables on device ownership and digital skills).

External: (Planned) Scraped Yelp/Google Maps data for private "Third Space" density.

🏗️ Repository Structure
Plaintext

seattle-public-life-analysis/
├── data/
│   ├── raw/             # Original CSVs (Immutable)
│   ├── processed/       # Cleaned and merged master datasets
├── seattle_vitality/    # Source code for data loaders and cleaning
├── notebooks/           # Jupyter notebooks for EDA and modeling
├── scripts/             # Python scripts for automated joining/scraping
└── requirements.txt     # Python dependencies
🛠️ Installation & Setup
Clone the repo:

Bash

git clone https://github.com/AidanGrambihler/seattle-public-life-analysis.git
cd seattle-public-life-analysis
Install Dependencies:

Bash

pip install -r requirements.txt
Data Placement: Ensure the raw Seattle Open Data CSV files are placed in data/raw/.

## 🧪 Current Status: Data Harmonization & Engineering
We have completed the **Longitudinal Survey Pipeline**. This involved bridging two disparate datasets (2018 and 2023 Digital Equity Surveys) into a unified analysis format.

### Key Achievements:
- **Schema Alignment:** Mapped inconsistent variable names (e.g., `q11a_x` vs `Q10rx`) to a standardized "Human Readable" schema.
- **Categorical Harmonization:** Unfied the 1-7 Internet Reliability scale and reconciled diverging Ethnicity and Income codes across a 5-year gap.
- **Feature Engineering:** Developed a scanning algorithm to transform multi-column survey responses into a single, searchable `usage_locations` attribute.

## ⚙️ Data Pipeline
1. **`scripts/02b_standardize_surveys.py`**:
   - Cleans and sanitizes ZIP codes (handling numeric/string inconsistencies).
   - Maps raw numeric survey codes to descriptive categories (Income, Ethnicity, Reliability).
   - Standardizes reported internet usage locations into a unified string format.
   - **Output:** `data/processed/standardized_tech_surveys.csv`

2. **`scripts/03_merge_data.py`** (In Progress):
   - Merging "Street Vitality" (SDOT Observation Data) with "Digital Equity" (Survey Data).
   - Mapping SDOT observation sites to ZIP-level survey insights.

## 📊 Data Audit & Longitudinal Strategy
Before finalizing the master merge, a pre-flight audit (`scripts/00_data_audit.py`) was implemented to verify temporal coverage. While the "Staying" observations are robust across both study years, the "Moving" (pedestrian flow) data showed a significant decline in the 2023 cycle:

| Dataset | 2018 Observations | 2023 Observations |
| :--- | :---: | :---: |
| **Staying** (Behavior) | 6,537 | 4,512 |
| **Moving** (Flow) | 1,728 | 0* |
*\*Note: Only 99 Moving observations were recorded in 2022, with none in 2023.*

**Methodological Pivot:** To maintain longitudinal rigor for the "Option A" strategy, this project utilizes the **Digital-to-Social Ratio (DSR)** as the primary dependent variable. This allows for a direct comparison of public space *intent* (Utility vs. Social interaction) without the bias of inconsistent pedestrian flow counts.

## 🚀 Getting Started
1. **Data Placement:** Place `tech_survey_2023.csv`, `tech_survey_2018.csv`, and `staying.csv` in `data/raw/`.
2. **References:** See the `references/` folder for the original City of Seattle codebooks used for mapping.
3. **Execution:**
   ```bash
   python scripts/02b_standardize_surveys.py