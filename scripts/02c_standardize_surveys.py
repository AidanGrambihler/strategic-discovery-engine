"""
SURVEY STANDARDIZATION & HARMONIZATION
--------------------------------------
Purpose:
1. Harmonizes 2018 and 2023 Seattle Tech Surveys into a single longitudinal schema.
2. Inverts the Reliability Scale so that higher scores (5) indicate better infrastructure.
3. Maps categorical data (Ethnicity, Gender, Usage Locations) to unified labels.
4. Extracts 'Societal Impact' sentiment regarding technology.

Note: Income buckets are kept in nominal dollars per year to maintain
the raw survey structure, rather than applying inflation adjustment.
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path

# 1. Setup Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("survey_standardization.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 2. Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"
processed_path = base_path / "data" / "processed"

# --- MAPPING DICTIONARIES ---
# Reliability Scale: INVERTED (5 is Best, 1 is Worst)
reliability_desc_map = {5: "Completely Adequate", 4: "Mostly Adequate", 3: "Sometimes Adequate", 2: "Rarely Adequate", 1: "Not Adequate"}

# Income Brackets (Nominal per year)
income_map = {1: "Below $25-27k", 2: "$25k-$49k", 3: "$50k-$74k", 4: "$75k-$99k", 5: "$100k-$149k", 6: "$150k-$199k", 7: "$200k+"}

#Ethnicity and gender mapping
eth_map_2018 = {1: "White", 2: "African American", 3: "Asian", 4: "NH/PI", 5: "AI/AN", 6: "Hispanic", 7: "Other", 8: "Refused", 9: "Mixed", 0: "No Response"}
eth_map_2023 = {1: "Asian", 2: "African American", 3: "Middle Eastern", 4: "AI/AN", 5: "NH/PI", 6: "White", 7: "Other", 8: "Mixed", 9: "Refused", 10: "Hispanic"}
gender_map_2018 = {1: "Male", 2: "Female", 3: "Non-binary", 0: "No Response", 4: "No Response"}

# Location Legend for Usage
loc_legend = {1: "Home", 2: "Work", 3: "School", 4: "Library", 5: "Community Center", 6: "Religious/Cultural Center", 7: "Friend/Relative Home", 8: "Public Plaza/Airport", 9: "Business/Coffee Shop", 10: "Other", 11: "Do Not Use Internet", 12: "N/A"}


# --- HELPER FUNCTIONS ---

def clean_zip(z):
    z_str = str(z).replace(',', '').split('.')[0].strip()
    return z_str.zfill(5) if z_str.isdigit() else "00000"


def harmonize_reliability(val, year):
    try:
        val = int(val)
        is_na = (year == 2018 and val in [8, 9]) or (year == 2023 and val == 6)
        is_null = (year == 2018 and val == 0) or (year == 2023 and val == 7)
        if is_na: return np.nan, "Not Applicable"
        if is_null: return np.nan, "No Response"
        if 1 <= val <= 5:
            inverted = 6 - val
            return inverted, reliability_desc_map[inverted]
    except: pass
    return np.nan, "No Response"

def harmonize_impact(val):
    """Aligns technology societal impact: 1 (Positive) to 5 (Harmful)."""
    try:
        v = int(val)
        return v if 1 <= v <= 5 else np.nan
    except:
        return np.nan


# --- GENDER & LOCATION HELPERS ---
def extract_gender_2023(row):
    if row.get('Q30r1') == 1: return "Female"
    if row.get('Q30r2') == 1: return "Male"
    if row.get('Q30r3') == 1: return "Non-binary"
    return "No Response"


def get_usage_metrics(row, year):
    if year == 2018:
        found_codes = [int(row.get(f'q11a_{i}')) for i in range(1, 12) if
                       pd.notna(row.get(f'q11a_{i}')) and int(row.get(f'q11a_{i}')) in loc_legend]
    else:
        found_codes = [i for i in range(1, 13) if row.get(f'Q10r{i}') == 1]

    loc_names = [loc_legend[c] for c in sorted(found_codes)]
    not_home_count = len([c for c in found_codes if c != 1])
    return ", ".join(loc_names) if loc_names else "None", not_home_count

def harmonize_access(val):
    """Maps access to 1 (Yes) and 0 (No/Refused)."""
    try:
        v = int(val)
        return 1 if v == 1 else 0
    except:
        return 0

# --- MAIN PROCESSING ---

def process_year(year, file_name, zip_col, gender_extractor, ethnicity_map, impact_col):
    logger.info(f"Processing {year} Survey...")
    df = pd.read_csv(raw_path / file_name, low_memory=False)

    # Calculate new columns in a dictionary to avoid fragmentation
    new_cols = {}
    new_cols['survey_year'] = [year] * len(df)
    new_cols['zip_code'] = df[zip_col].apply(clean_zip)
    # Add to the new_cols dictionary
    new_cols['has_internet_access'] = df['q1' if year == 2018 else 'Q1'].apply(harmonize_access)
    rel_res = df['q6' if year == 2018 else 'Q6'].apply(lambda x: harmonize_reliability(x, year))
    new_cols['reliability_score'], new_cols['reliability_desc'] = zip(*rel_res)
    new_cols['societal_impact_score'] = df[impact_col].apply(harmonize_impact)

    usage_res = df.apply(lambda row: get_usage_metrics(row, year), axis=1)
    new_cols['usage_locations'], new_cols['num_usage_locations_not_home'] = zip(*usage_res)

    if year == 2023:
        new_cols['gender_group'] = df.apply(gender_extractor, axis=1)
    else:
        new_cols['gender_group'] = pd.to_numeric(df['Gender'], errors='coerce').map(gender_map_2018).fillna(
            'No Response')

    new_cols['income_group'] = pd.to_numeric(df['INCOME'], errors='coerce').map(income_map)
    new_cols['ethnicity_group'] = pd.to_numeric(df['ethnicity' if year == 2018 else 'Ethnicity'], errors='coerce').map(
        ethnicity_map)

    # Create a new DataFrame from the dictionary and concat once
    df_new = pd.DataFrame(new_cols)
    return df_new


def run_standardization():
    # 2023
    df_23_final = process_year(2023, "tech_survey_2023.csv", "ZIPCode", extract_gender_2023, eth_map_2023, "Q23")

    # 2018
    df_18_final = process_year(2018, "tech_survey_2018.csv", "qzip", None, eth_map_2018, "q22_2")

    # Combine
    master_df = pd.concat([df_18_final, df_23_final], ignore_index=True)
    master_df['zip_respondent_count'] = master_df.groupby(['zip_code', 'survey_year'])['zip_code'].transform('count')

    processed_path.mkdir(parents=True, exist_ok=True)
    master_df.to_csv(processed_path / "standardized_tech_surveys.csv", index=False)
    logger.info(f"Success! Total longitudinal rows: {len(master_df)}")


if __name__ == "__main__":
    run_standardization()