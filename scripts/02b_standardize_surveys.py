import pandas as pd
import numpy as np
from pathlib import Path

# Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"
processed_path = base_path / "data" / "processed"

# --- 1. HARMONIZED MAPPING DICTIONARIES ---

# Reliability Scale (Harmonized)
reliability_map = {
    1: "Completely Adequate", 2: "Mostly Adequate", 3: "Sometimes Adequate",
    4: "Rarely Adequate", 5: "Not Adequate", 6: "N/A / No Access", 7: "No Response / Refused"
}

# Income Brackets (Bridging 2018 & 2023)
income_map = {
    1: "Below $25-27k", 2: "$25k-$49k", 3: "$50k-$74k",
    4: "$75k-$99k", 5: "$100k-$149k", 6: "$150k-$199k", 7: "$200k+"
}

# Ethnicity Maps (YEAR SPECIFIC)
eth_map_2018 = {
    1: "White", 2: "African American", 3: "Asian",
    4: "NH/PI", 5: "AI/AN", 6: "Hispanic",
    7: "Other", 8: "Refused", 9: "Mixed", 0: "No Response"
}

eth_map_2023 = {
    1: "Asian", 2: "African American", 3: "Middle Eastern",
    4: "AI/AN", 5: "NH/PI", 6: "White",
    7: "Other", 8: "Mixed", 9: "Refused", 10: "Hispanic"
}

# Location Legend
loc_legend = {
    1: "Home", 2: "Work", 3: "School", 4: "Library", 5: "Community Center",
    6: "Religious/Cultural Center", 7: "Friend/Relative Home", 8: "Public Plaza/Airport",
    9: "Business/Coffee Shop", 10: "Other", 11: "Do Not Use Internet", 12: "N/A"
}


# --- 2. HELPER FUNCTIONS ---

def clean_zip(z):
    z_str = str(z).replace(',', '').split('.')[0].strip()
    return z_str.zfill(5) if z_str.isdigit() else "00000"


def get_usage_locations_2018(row):
    found_codes = set()
    for i in range(1, 12):
        col = f'q11a_{i}'
        val = row.get(col)
        if pd.notna(val) and val in loc_legend:
            found_codes.add(int(val))
    return ", ".join([loc_legend[c] for c in sorted(list(found_codes))]) if found_codes else "None"


def get_usage_locations_2023(row):
    found_labels = [loc_legend[i] for i in range(1, 13) if row.get(f'Q10r{i}') == 1]
    return ", ".join(found_labels) if found_labels else "None"


# --- 3. MAIN PROCESSING ---

def process_surveys():
    print("💎 Polishing Master Dataset: Applying Labels & Harmonizing Scales...")

    # --- 2023 ---
    df_23 = pd.read_csv(raw_path / "tech_survey_2023.csv", low_memory=False)
    df_23['survey_year'] = 2023
    df_23['zip_code'] = df_23['ZIPCode'].apply(clean_zip)
    df_23['has_home_internet'] = df_23['Q1'].map({1: 'Yes', 2: 'No'}).fillna('Unknown')
    df_23['device_count_owned'] = pd.to_numeric(df_23['Q4OwnSum'], errors='coerce').fillna(0).astype(int)

    # Apply 2023 Specific Maps
    df_23['reliability_score'] = pd.to_numeric(df_23['Q6'], errors='coerce').replace({6: 6, 7: 7})
    df_23['reliability_desc'] = df_23['reliability_score'].map(reliability_map)
    df_23['income_group'] = pd.to_numeric(df_23['INCOME'], errors='coerce').map(income_map)
    df_23['ethnicity_group'] = pd.to_numeric(df_23['Ethnicity'], errors='coerce').map(eth_map_2023)
    df_23['usage_locations'] = df_23.apply(get_usage_locations_2023, axis=1)

    # --- 2018 ---
    df_18 = pd.read_csv(raw_path / "tech_survey_2018.csv", low_memory=False)
    df_18['survey_year'] = 2018
    df_18['zip_code'] = df_18['qzip'].apply(clean_zip)
    df_18['has_home_internet'] = df_18['q1'].map({1: 'Yes', 2: 'No'}).fillna('Unknown')
    df_18['device_count_owned'] = pd.to_numeric(df_18['q2bOwnSum'], errors='coerce').fillna(0).astype(int)

    # Apply 2018 Specific Maps
    df_18['reliability_score'] = pd.to_numeric(df_18['q6'], errors='coerce').replace({8: 6, 9: 6, 0: 7})
    df_18['reliability_desc'] = df_18['reliability_score'].map(reliability_map)
    df_18['income_group'] = pd.to_numeric(df_18['INCOME'], errors='coerce').map(income_map)
    df_18['ethnicity_group'] = pd.to_numeric(df_18['ethnicity'], errors='coerce').map(eth_map_2018)
    df_18['usage_locations'] = df_18.apply(get_usage_locations_2018, axis=1)

    # --- Combine & Order ---
    final_cols = ['zip_code', 'survey_year', 'has_home_internet', 'device_count_owned',
                  'reliability_score', 'reliability_desc', 'usage_locations',
                  'income_group', 'ethnicity_group']

    master_df = pd.concat([df_18[final_cols], df_23[final_cols]], ignore_index=True)

    # Save
    processed_path.mkdir(parents=True, exist_ok=True)
    master_df.to_csv(processed_path / "standardized_tech_surveys.csv", index=False)

    print(f"✅ Master File Ready! Rows: {len(master_df)}")
    print(f"Ethnicity Check: {master_df['ethnicity_group'].unique()[:5]}")


if __name__ == "__main__":
    process_surveys()