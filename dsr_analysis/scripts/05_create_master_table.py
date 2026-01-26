"""
FILE: 05_create_master_table.py
PROJECT: Seattle Digital Equity & Public Life Study
DESCRIPTION: Fuses residential survey metrics (Equity) with public behavioral
             observations (Vitality). Generates the DSR (Digital-to-Social Ratio).
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from dsr_analysis import (
    get_categorical_pcts,
    map_years_to_eras,
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

def map_to_bucket(val, year):
    """Reverse-maps continuous median to categorical bucket for readability."""
    mid_map = MIDPOINT_MAP_2018 if year == 2018 else MIDPOINT_MAP_2023
    label_map = INCOME_LABELS_2018 if year == 2018 else INCOME_LABELS_2023
    closest_key = min(mid_map.keys(), key=lambda k: abs(mid_map[k] - val))
    return label_map[closest_key]

def main():
    logger.info("Initializing Master Table fusion...")

    try:
        # --- 1. LOAD ASSETS ---
        crosswalk = pd.read_csv(PROCESSED_DIR / "location_to_zip_crosswalk.csv")
        surveys = pd.read_csv(PROCESSED_DIR / "standardized_tech_surveys.csv")
        staying = pd.read_csv(RAW_DIR / "staying.csv", low_memory=False)

        for df_tmp in [crosswalk, surveys]:
            df_tmp['zip_code'] = df_tmp['zip_code'].astype(str).str.zfill(5)

        # --- 2. SURVEY AGGREGATION (RESIDENTIAL EQUITY) ---
        logger.info("Aggregating residential equity benchmarks...")
        zip_equity = surveys.groupby(['zip_code', 'survey_year']).agg(
            res_n_respondents=('zip_code', 'count'),
            res_avg_reliability=('reliability_score', 'mean'),
            res_avg_societal_impact=('societal_impact_score', 'mean'),
            res_median_income=('income_continuous', 'median'),
            res_pct_internet_access=('has_internet_access', lambda x: x.mean() * 100)
        ).reset_index()

        zip_equity['res_median_income_bucket'] = zip_equity.apply(
            lambda row: map_to_bucket(row['res_median_income'], row['survey_year']), axis=1
        )

        # Merge Percentages (Ethnicity & Gender)
        for func_name, prefix in [(get_categorical_pcts, 'res_pct_eth'), (get_categorical_pcts, 'res_pct_gen')]:
            col = 'ethnicity_group' if 'eth' in prefix else 'gender_group'
            pcts = get_categorical_pcts(surveys, col, prefix)
            zip_equity = zip_equity.merge(pcts, on=['zip_code', 'survey_year'], how='left')

        # --- 3. BEHAVIORAL AGGREGATION (PUBLIC VITALITY) ---
        logger.info("Collapsing behavioral observations into ZIP-Eras...")
        staying['actual_year'] = pd.to_datetime(staying['staying_time_start']).dt.year
        staying['survey_year'] = map_years_to_eras(staying['actual_year'])

        obs_with_zips = (staying.dropna(subset=['survey_year'])
                         .merge(crosswalk, on='location_id', how='inner'))
        obs_with_zips['zip_code'] = obs_with_zips['zip_code'].astype(str).str.zfill(5)

        for tod in ['morning', 'midday', 'evening']:
            obs_with_zips[f'obs_raw_count_{tod}'] = (
                obs_with_zips['staying_time_of_day'].str.lower() == tod
            ).astype(int)

        zip_behavior = obs_with_zips.groupby(['zip_code', 'survey_year']).agg(
            obs_total_stays=('staying_row_total', 'sum'),
            obs_digital_users=('using_electronics', 'sum'),
            obs_social_users=('talking_to_others', 'sum'),
            obs_avg_temp=('staying_temperature', 'mean'),
            obs_count_morning=('obs_raw_count_morning', 'sum'),
            obs_count_midday=('obs_raw_count_midday', 'sum'),
            obs_count_evening=('obs_raw_count_evening', 'sum')
        ).reset_index()

        # Feature Engineering: DSR
        zip_behavior['obs_dsr'] = zip_behavior['obs_digital_users'] / (zip_behavior['obs_social_users'] + 1)
        zip_behavior['obs_pct_digital'] = (zip_behavior['obs_digital_users'] / zip_behavior['obs_total_stays'] * 100)

        # --- 4. DATA FUSION & QUALITY CONTROL ---
        # INNER JOIN: We only keep ZIP-Eras where we have BOTH survey and behavioral data
        master_table = pd.merge(zip_equity, zip_behavior, on=['zip_code', 'survey_year'], how='inner')

        # Fill missing demographic percentages with 0 (Standard practice for Sparse Categoricals)
        pct_cols = [c for c in master_table.columns if 'res_pct_' in c]
        master_table[pct_cols] = master_table[pct_cols].fillna(0)

        # Define Robustness
        master_table['is_robust'] = (master_table['obs_total_stays'] >= 50) & (master_table['res_n_respondents'] >= 30)

        # Join Leakage Audit
        lost_zips = set(zip_equity['zip_code']) - set(master_table['zip_code'])
        if lost_zips:
            logger.warning(f"Join Leakage: {len(lost_zips)} ZIPs had survey data but no behavioral observations.")

        # Save
        output_path = PROCESSED_DIR / "master_table.csv"
        master_table.round(4).to_csv(output_path, index=False)

        logger.info(f"Fusion successful. {len(master_table)} neighborhood-era rows generated.")

    except Exception as e:
        logger.error(f"Critical error during master table fusion: {e}")
        raise

if __name__ == "__main__":
    main()