# Mappings derived from City of Seattle Digital Equity Codebooks (2018 & 2023).
# Original documents located in the /references folder.

import pandas as pd
from pathlib import Path

base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"
processed_path = base_path / "data" / "processed"

# 1. THE COMPREHENSIVE SEMANTIC MAP
# We translate the most important "Vitality" and "Equity" columns manually
semantic_map_2023 = {
    'ZIPCode': 'zip_code',
    'Q1': 'has_home_internet',
    'Q3': 'internet_outage_past_year',
    'Q4OwnSum': 'devices_owned_total',
    'Q4_1tot': 'count_desktops',
    'Q4_2tot': 'count_laptops',
    'Q4_3tot': 'count_tablets',
    'Q4_4tot': 'count_smartphones',
    'Q5ASum': 'internet_provider_type',
    'q5bSum': 'monthly_internet_cost',
    'Q6': 'connection_adequacy_score',
    'Q7': 'download_speed_category',
    'Q8': 'frequency_of_slow_service',
    'Q10r1': 'use_loc_home',
    'Q10r4': 'use_loc_library',
    'Q10r8': 'use_loc_public_plaza', # <--- KEY VITALITY LINK
    'Q10r9': 'use_loc_coffee_shop',
    'INCOME': 'income_group',
    'Ethnicity': 'ethnicity_group',
    'HHSIZE': 'household_size',
    'Education': 'education_level'
}

# 2. THE 2018 EQUIVALENTS
# We map the 2018 codes to the SAME names as above for a perfect stack
semantic_map_2018 = {
    'qzip': 'zip_code',
    'q1': 'has_home_internet',
    'q3': 'internet_outage_past_year',
    'q2bOwnSum': 'devices_owned_total',
    'q5aSum': 'internet_provider_type',
    'q5bSum': 'monthly_internet_cost',
    'q6': 'connection_adequacy_score',
    'q7': 'download_speed_category',
    'q8': 'frequency_of_slow_service',
    'q10a_1': 'use_loc_home',
    'q10a_4': 'use_loc_library',
    'q10a_8': 'use_loc_public_plaza',
    'q10a_9': 'use_loc_coffee_shop',
    'INCOME': 'income_group',
    'ethnicity': 'ethnicity_group',
    'HHSize': 'household_size',
    'EDUC': 'education_level'
}

def standardize_and_stack():
    print("🧪 Building Standardized Longitudinal Dataset...")

    # Process 2023
    df_23 = pd.read_csv(raw_path / "tech_survey_2023.csv", low_memory=False)
    # We keep only the columns we mapped to keep the project focused
    df_23_clean = df_23[list(semantic_map_2023.keys())].rename(columns=semantic_map_2023)
    df_23_clean['survey_year'] = 2023

    # Process 2018
    df_18 = pd.read_csv(raw_path / "tech_survey_2018.csv", low_memory=False)
    # Filter 2018 to the same set of questions
    df_18_clean = df_18[list(semantic_map_2018.keys())].rename(columns=semantic_map_2018)
    df_18_clean['survey_year'] = 2018

    # Stack them
    master_survey = pd.concat([df_18_clean, df_23_clean], ignore_index=True)

    # Clean Zip Codes
    master_survey['zip_code'] = pd.to_numeric(master_survey['zip_code'], errors='coerce').fillna(0).astype(int)

    # Save
    master_survey.to_csv(processed_path / "standardized_tech_surveys.csv", index=False)
    print(f"✅ Master Survey Created with {master_survey.shape[1]} descriptive columns.")

if __name__ == "__main__":
    standardize_and_stack()