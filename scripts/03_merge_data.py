"""
MASTER DATA FUSION & FEATURE ENGINEERING
----------------------------------------
Purpose:
1. Aggregates standardized survey data into neighborhood-level equity metrics.
2. Lumps 'Staying' behavioral data into study eras (2018/19 -> 2018, 2022/23 -> 2023).
3. Merges residential (res) and observational (obs) datasets by ZIP and Era.
4. Engineers the Digital-to-Social Ratio (DSR) and statistical robustness flags.

Output: data/processed/master_vitality_index.csv
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path

# 1. Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("data_fusion_v2.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 2. Setup Paths
base_path = Path(__file__).resolve().parent.parent
processed_path = base_path / "data" / "processed"
raw_path = base_path / "data" / "raw"


def get_pct_df(df, group_col, prefix):
    """Calculates distribution percentages for categorical variables."""
    counts = pd.crosstab([df['zip_code'], df['survey_year']], df[group_col])
    pcts = (counts.div(counts.sum(axis=1), axis=0) * 100)
    pcts.columns = [f"{prefix}_{str(c).lower().replace(' ', '_').replace('/', '_').replace('-', '_')}" for c in
                    pcts.columns]
    return pcts.reset_index()


def merge_vitality_data():
    logger.info("Initializing Fusing of Surveys and Behavioral Data (Demographic Pivot)")

    # --- 1. LOAD DATA ---
    try:
        df_crosswalk = pd.read_csv(processed_path / "location_to_zip_crosswalk.csv")
        df_survey = pd.read_csv(processed_path / "standardized_tech_surveys.csv")
        df_staying = pd.read_csv(raw_path / "staying.csv", low_memory=False)
    except FileNotFoundError as e:
        logger.critical(f"Required file missing for merge: {e}")
        return

    # Standardize ZIP formats
    for df in [df_crosswalk, df_survey]:
        df['zip_code'] = df['zip_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(5)

    # --- 2. AGGREGATE SURVEYS (Residential Ground Truth) ---
    logger.info("Aggregating residential equity and demographics")

    income_numeric_map = {
        "Below $25-27k": 1, "$25k-$49k": 2, "$50k-$74k": 3,
        "$75k-$99k": 4, "$100k-$149k": 5, "$150k-$199k": 6, "$200k+": 7
    }
    df_survey['res_income_score'] = df_survey['income_group'].map(income_numeric_map)

    zip_equity = df_survey.groupby(['zip_code', 'survey_year']).agg(
        res_n_respondents=('zip_code', 'count'),
        res_avg_reliability=('reliability_score', 'mean'),
        res_avg_societal_impact=('societal_impact_score', 'mean'),
        res_avg_locations_not_home=('num_usage_locations_not_home', 'mean'),
        res_median_income_bracket=('res_income_score', 'median'),
        res_pct_access = ('has_internet_access', lambda x: x.mean() * 100)
    ).reset_index()

    # Residential Demographics (The "Who")
    res_eth_pcts = get_pct_df(df_survey, 'ethnicity_group', 'res_pct_eth')
    res_gen_pcts = get_pct_df(df_survey, 'gender_group', 'res_pct_gen')

    zip_equity = zip_equity.merge(res_eth_pcts, on=['zip_code', 'survey_year'], how='left')
    zip_equity = zip_equity.merge(res_gen_pcts, on=['zip_code', 'survey_year'], how='left')

    # --- 3. PROCESS STAYING DATA (Strictly Behavioral) ---
    logger.info("Processing behavioral observations (Usage & Timing only)")

    df_staying['actual_year'] = pd.to_datetime(df_staying['staying_time_start']).dt.year
    era_map = {2018: 2018, 2019: 2018, 2022: 2023, 2023: 2023}
    df_staying['survey_year'] = df_staying['actual_year'].map(era_map)
    df_staying = df_staying.dropna(subset=['survey_year']).copy()

    staying_with_zips = df_staying.merge(df_crosswalk, on='location_id', how='inner')

    # Prep Time of Day dummies
    for tod in ['morning', 'midday', 'evening']:
        staying_with_zips[f'obs_raw_time_{tod}'] = (
                staying_with_zips['staying_time_of_day'].str.lower() == tod
        ).astype(int)

    # Aggregate behavioral data - NO RACE/GENDER INCLUDED HERE
    zip_behavior = staying_with_zips.groupby(['zip_code', 'survey_year']).agg(
        obs_total_stays=('staying_row_total', 'sum'),
        obs_digital_users=('using_electronics', 'sum'),
        obs_social_users=('talking_to_others', 'sum'),
        obs_avg_temp=('staying_temperature', 'mean'),
        obs_count_morning=('obs_raw_time_morning', 'sum'),
        obs_count_midday=('obs_raw_time_midday', 'sum'),
        obs_count_evening=('obs_raw_time_evening', 'sum')
    ).reset_index()

    # Calculate Time percentages
    for tod in ['morning', 'midday', 'evening']:
        zip_behavior[f'obs_pct_time_{tod}'] = (
                zip_behavior[f'obs_count_{tod}'] / zip_behavior['obs_total_stays'] * 100
        ).round(2)

    # --- 4. FEATURE ENGINEERING ---
    logger.info("Engineering Digital-to-Social Ratio (DSR)")
    zip_behavior['obs_dsr'] = zip_behavior['obs_digital_users'] / (zip_behavior['obs_social_users'] + 1)
    zip_behavior['obs_pct_digital'] = (zip_behavior['obs_digital_users'] / zip_behavior['obs_total_stays'] * 100).round(
        2)

    # --- 5. THE MASTER JOIN ---
    logger.info("Fusing residential and observational datasets")
    master_index = pd.merge(zip_equity, zip_behavior, on=['zip_code', 'survey_year'], how='inner')

    # Statistical Robustness Flag
    master_index['is_robust'] = (
            (master_index['obs_total_stays'] >= 30) &
            (master_index['res_n_respondents'] >= 20)
    )

    master_index = master_index.round(3)
    output_path = processed_path / "master_vitality_index.csv"
    master_index.to_csv(output_path, index=False)
    logger.info(f"Master Index (V2) created. Shape: {master_index.shape}")


if __name__ == "__main__":
    merge_vitality_data()