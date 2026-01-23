Seattle Urban Vitality & Digital Equity Index
An analysis of physical public life and digital infrastructure reliance.

📌 Project Overview
This project investigates the relationship between neighborhood-level digital access and the actual observed behavior of people in public spaces. By anchoring 2023 SDOT Public Life observation data with the Technology Access and Adoption Survey, we aim to identify if public spaces serve as "critical digital hubs" in neighborhoods with low home-broadband adoption.

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

🧪 Current Status: Data Engineering
Currently performing a Many-to-One Join between the 17,000+ observation rows and the 132 unique location sites to create a "Vitality Master Table."
