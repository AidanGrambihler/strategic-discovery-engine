"""
FILE: 04_clean_surveys.py
PROJECT: Seattle Digital Equity & Public Life Study
DESCRIPTION: Harmonizes 2018 and 2023 Technology Access and Adoption surveys.
             Standardizes reliability scales, demographics, and usage metrics.
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from dsr_analysis import (
    clean_zip_code,
    get_usage_metrics,
    INCOME_LABELS_2018,
    INCOME_LABELS_2023,
    MIDPOINT_MAP_2018,
    MIDPOINT_MAP_2023
)

# 1. Setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# 2. Schema Crosswalks (Normalized for Longitudinal Parity)
# These ensure that "Hispanic" in 2018 and 10 in 2023 result in the same string.
ETH_MAP_2018 = {1: "White", 2: "African American", 3: "Asian", 4: "NH/PI", 5: "AI/AN", 6: "Hispanic", 7: "Other", 8: "Refused", 9: "Mixed", 0: "No Response"}
ETH_MAP_2023 = {1: "Asian", 2: "African American", 3: "Middle Eastern", 4: "AI/AN", 5: "NH/PI", 6: "White", 7: "Other", 8: "Mixed", 9: "Refused", 10: "Hispanic"}

def harmonize_reliability(val, year):
    """Inverts scale: Original (1=Reliable, 5=Not) -> Target (5=High, 1=Low)."""
    try:
        v = int(val)
        if (year == 2018 and v in [0, 8, 9]) or (year == 2023 and v in [6, 7]):
            return np.nan
        return 6 - v if 1 <= v <= 5 else np.nan
    except (ValueError, TypeError):
        return np.nan

def process_year(year, filename, zip_col, eth_map, impact_col):
    """Processes a single survey year into the standardized schema."""
    logger.info(f"Processing {year} data from {filename}...")

    file_path = RAW_DIR / filename
    if not file_path.exists():
        logger.error(f"Missing file: {filename}")
        return pd.DataFrame()

    df = pd.read_csv(file_path, low_memory=False)
    data = {}
    data['survey_year'] = [year] * len(df)
    data['zip_code'] = df[zip_col].apply(clean_zip_code)

    # 1. Access & Reliability
    access_col = 'q1' if year == 2018 else 'Q1'
    data['has_internet_access'] = (pd.to_numeric(df[access_col], errors='coerce') == 1).astype(int)

    rel_col = 'q6' if year == 2018 else 'Q6'
    data['reliability_score'] = df[rel_col].apply(lambda x: harmonize_reliability(x, year))

    # 2. Usage Behaviors (The 'Dependent' proxy)
    usage_res = df.apply(lambda row: get_usage_metrics(row, year), axis=1)
    data['usage_locations'], data['num_usage_locations_not_home'] = zip(*usage_res)

    # 3. Income Midpoint Imputation (Critical for Script 07)
    inc_label_map = INCOME_LABELS_2018 if year == 2018 else INCOME_LABELS_2023
    inc_midpoint_map = MIDPOINT_MAP_2018 if year == 2018 else MIDPOINT_MAP_2023
    raw_income = pd.to_numeric(df['INCOME'], errors='coerce')

    data['income_group'] = raw_income.map(inc_label_map)
    data['income_continuous'] = raw_income.map(inc_midpoint_map)

    # 4. Ethnicity Normalization
    eth_col = 'ethnicity' if year == 2018 else 'Ethnicity'
    data['ethnicity_group'] = pd.to_numeric(df[eth_col], errors='coerce').map(eth_map)

    # 5. Gender Logic
    if year == 2023:
        if 'Q30r1' in df.columns:
            data['gender_group'] = np.where(df['Q30r1']==1, "Female",
                                   np.where(df['Q30r2']==1, "Male",
                                   np.where(df['Q30r3']==1, "Non-binary", "Other/No Response")))
        else:
            data['gender_group'] = "No Response"
    else:
        gender_map_2018 = {1: "Male", 2: "Female", 3: "Non-binary", 0: "No Response", 4: "No Response"}
        data['gender_group'] = pd.to_numeric(df['Gender'], errors='coerce').map(gender_map_2018).fillna("No Response")

    # 6. Societal Impact
    data['societal_impact_score'] = pd.to_numeric(df[impact_col], errors='coerce')

    return pd.DataFrame(data)

def main():
    # Execute the pipeline
    df_18 = process_year(2018, "tech_survey_2018.csv", "qzip", ETH_MAP_2018, "q22_2")
    df_23 = process_year(2023, "tech_survey_2023.csv", "ZIPCode", ETH_MAP_2023, "Q23")

    master_df = pd.concat([df_18, df_23], ignore_index=True)

    # Feature Engineering: Weighting
    master_df['zip_respondent_count'] = master_df.groupby(['zip_code', 'survey_year'])['zip_code'].transform('count')

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    master_df.to_csv(PROCESSED_DIR / "standardized_tech_surveys.csv", index=False)

    logger.info(f"Standardization Complete. {len(master_df)} records across {master_df['zip_code'].nunique()} ZIPs.")

if __name__ == "__main__":
    main()