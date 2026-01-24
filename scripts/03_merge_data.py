import pandas as pd
from pathlib import Path

# Setup Paths
base_path = Path(__file__).resolve().parent.parent
processed_path = base_path / "data" / "processed"
raw_path = base_path / "data" / "raw"


def merge_vitality_data():
    print("🚀 Fusing Surveys and Staying data into a Longitudinal Master Index...")

    # 1. LOAD CROSSWALK & SURVEYS
    df_crosswalk = pd.read_csv(processed_path / "location_to_zip_crosswalk.csv")
    df_crosswalk['zip_code'] = df_crosswalk['zip_code'].astype(str).str.replace('\.0$', '', regex=True).str.zfill(5)

    df_survey = pd.read_csv(processed_path / "standardized_tech_surveys.csv")
    df_survey['zip_code'] = df_survey['zip_code'].astype(str).str.replace('\.0$', '', regex=True).str.zfill(5)

    # Map the string income groups back to a 1-7 scale for modeling
    income_numeric_map = {
        "Below $25-27k": 1, "$25k-$49k": 2, "$50k-$74k": 3,
        "$75k-$99k": 4, "$100k-$149k": 5, "$150k-$199k": 6, "$200k+": 7
    }

    df_survey['income_score'] = df_survey['income_group'].map(income_numeric_map)

    # 2. AGGREGATE SURVEYS (The "Need" Context)
    print("📊 Calculating refined equity metrics (Access, Devices, Ethnicity)...")

    # A. Feature Engineering within the Survey Data
    # Convert 'Yes' to 1 and 'No' to 0
    df_survey['has_internet_binary'] = (df_survey['has_home_internet'] == 'Yes').astype(int)

    # Convert the comma-separated string into a count of locations
    # We handle NaNs by filling with an empty string first
    df_survey['usage_locations_count'] = df_survey['usage_locations'].fillna('').apply(
        lambda x: len([i for i in x.split(',') if i.strip()]) if x else 0
    )

    # B. Aggregating Numeric & Access Columns
    zip_equity = df_survey.groupby(['zip_code', 'survey_year']).agg(
        num_survey_respondents=('zip_code', 'count'),
        avg_home_internet_reliability=('reliability_score', 'mean'),
        median_income_bracket=('income_score', 'median'),
        pct_has_home_internet=('has_internet_binary', lambda x: (x.mean() * 100).round(2)),
        avg_device_count_owned=('device_count_owned', 'mean'),
        avg_usage_locations=('usage_locations_count', 'mean'),
        predominant_income_group=('income_group', lambda x: x.mode()[0] if not x.mode().empty else "Unknown"),
    ).reset_index()

    # C. Calculate Demographic Percentages (Ethnicity & Gender)
    def get_pct_df(df, group_col, prefix):
        counts = pd.crosstab([df['zip_code'], df['survey_year']], df[group_col])
        pcts = (counts.div(counts.sum(axis=1), axis=0) * 100)
        # Clean column names: pct_gen_female, pct_eth_asian, etc.
        pcts.columns = [f"{prefix}_{str(c).lower().replace(' ', '_').replace('/', '_').replace('-', '_')}" for c in
                        pcts.columns]
        return pcts.reset_index()

    eth_pcts = get_pct_df(df_survey, 'ethnicity_group', 'pct_eth')
    gen_pcts = get_pct_df(df_survey, 'gender_group', 'pct_gen')

    # D. Merge Demographic Percentages back into zip_equity
    zip_equity = pd.merge(zip_equity, eth_pcts, on=['zip_code', 'survey_year'], how='left')
    zip_equity = pd.merge(zip_equity, gen_pcts, on=['zip_code', 'survey_year'], how='left')

    # E. UNIFORM ROUNDING (All pct_ and avg_ columns to 2 decimal places)
    cols_to_round = [c for c in zip_equity.columns if c.startswith('pct_') or c.startswith('avg_')]
    zip_equity[cols_to_round] = zip_equity[cols_to_round].round(2)

    # 3. PROCESS STAYING DATA (The "Behavior" Action)
    df_staying = pd.read_csv(raw_path / "staying.csv", low_memory=False)

    # Convert to datetime and extract the actual calendar year
    df_staying['actual_year'] = pd.to_datetime(df_staying['staying_time_start']).dt.year

    # Define the "Era Mapping"
    # This groups years into the survey target buckets (2018 or 2023)
    era_map = {
        2018: 2018, 2019: 2018,
        2022: 2023, 2023: 2023
    }

    # Apply the mapping: create 'survey_year' based on our era assumptions
    df_staying['survey_year'] = df_staying['actual_year'].map(era_map)

    # Filter: Keep only the rows that fall into our defined eras (removes 2020, 2021, etc.)
    df_staying = df_staying.dropna(subset=['survey_year'])
    df_staying['survey_year'] = df_staying['survey_year'].astype(int)

    # Merge with crosswalk to get zip codes
    staying_with_zips = pd.merge(df_staying, df_crosswalk, on='location_id', how='inner')

    # --- NEW: Observational Race/Ethnicity Mapping ---
    # Gehl Protocol: A=Asian, B=Black, L=Latino, M=Multi, N=Native, P=Pacific, U=Unsure, W=White
    race_map = {
        'A': 'obs_race_asian', 'B': 'obs_race_black', 'L': 'obs_race_latino',
        'M': 'obs_race_multiple', 'N': 'obs_race_native', 'P': 'obs_race_pacific',
        'U': 'obs_race_unsure', 'W': 'obs_race_white'
    }

    # Create dummy columns for each race category
    for code, col_name in race_map.items():
        staying_with_zips[col_name] = (staying_with_zips['staying_race_ethnicity'] == code).astype(int)

    staying_with_zips['obs_gen_female'] = (staying_with_zips['staying_gender'] == 'Female').astype(int)
    staying_with_zips['obs_gen_male'] = (staying_with_zips['staying_gender'] == 'Male').astype(int)
    staying_with_zips['obs_gen_other_unsure'] = (staying_with_zips['staying_gender'] == 'Other_Unsure').astype(int)

    # Aggregate behavioral, weather, and observational demographics
    zip_behavior = staying_with_zips.groupby(['zip_code', 'survey_year']).agg(
        public_total_stays=('staying_row_total', 'sum'),
        digital_users=('using_electronics', 'sum'),
        social_users=('talking_to_others', 'sum'),
        # Weather
        avg_staying_temperature=('staying_temperature', 'mean'),
        # Observed Gender Totals
        obs_gen_female=('obs_gen_female', 'sum'),
        obs_gen_male=('obs_gen_male', 'sum'),
        obs_gen_other_unsure=('obs_gen_other_unsure', 'sum'),
        # Observed Race Totals
        obs_race_asian=('obs_race_asian', 'sum'),
        obs_race_black=('obs_race_black', 'sum'),
        obs_race_latino=('obs_race_latino', 'sum'),
        obs_race_multiple=('obs_race_multiple', 'sum'),
        obs_race_native=('obs_race_native', 'sum'),
        obs_race_pacific=('obs_race_pacific', 'sum'),
        obs_race_unsure=('obs_race_unsure', 'sum'),
        obs_race_white=('obs_race_white', 'sum')
    ).reset_index()

    # Create Observed Percentages (for direct comparison to Residential Percentages)
    obs_cols = [c for c in zip_behavior.columns if c.startswith('obs_')]
    for col in obs_cols:
        pct_name = col.replace('obs_', 'obs_pct_')
        zip_behavior[pct_name] = (zip_behavior[col] / zip_behavior['public_total_stays'] * 100).round(2)

    # Round Temperature
    zip_behavior['avg_staying_temperature'] = zip_behavior['avg_staying_temperature'].round(1)

    # 4. FEATURE ENGINEERING: Digital-to-Social Ratio (DSR)
    # Formula: Digital / (Social + 1) -> The +1 prevents DivisionByZero errors
    # A DSR > 1 means the space is primarily a 'Digital Utility'
    # A DSR < 1 means the space is primarily 'Social'
    print("🧪 Engineering the Digital-to-Social Ratio (DSR)...")
    zip_behavior['public_dsr'] = zip_behavior['digital_users'] / (zip_behavior['social_users'] + 1)

    # Also calculate % of population doing each for a normalized view
    zip_behavior['public_pct_digital'] = (zip_behavior['digital_users'] / zip_behavior['public_total_stays']) * 100
    zip_behavior['public_pct_social'] = (zip_behavior['social_users'] / zip_behavior['public_total_stays']) * 100

    # ROUNDING FOR DISPLAY (Keep precision but clean the view)
    # This rounds to 2 decimal places
    cols_to_round = ['public_dsr', 'public_pct_digital', 'public_pct_social']
    zip_behavior[cols_to_round] = zip_behavior[cols_to_round].round(2)

    # INTEGER CONVERSION
    # This removes the .0 by converting to 'Int64' (which handles potential NaNs gracefully)
    cols_to_int = ['digital_users', 'social_users', 'public_total_stays']
    zip_behavior[cols_to_int] = zip_behavior[cols_to_int].fillna(0).astype(int)

    # --- TEMPORARY AUDIT: Verification of the "Lumping" Strategy ---
    print("\n🔍 ERA LUMPING AUDIT:")
    # Look at the raw counts per actual year
    raw_counts = df_staying.groupby('actual_year')['staying_row_total'].sum()
    print("Raw Stays by Calendar Year:")
    print(raw_counts)

    # Look at the lumped counts per survey era
    lumped_counts = zip_behavior.groupby('survey_year')['public_total_stays'].sum()
    print("\nLumped Stays by Survey Era:")
    print(lumped_counts)

    # Calculate the 'Gain'
    gain_2018 = lumped_counts.get(2018, 0) - raw_counts.get(2018, 0)
    gain_2023 = lumped_counts.get(2023, 0) - raw_counts.get(2023, 0)
    print(f"\n📈 Net Gain from Lumping: +{gain_2018} stays in 2018 era, +{gain_2023} stays in 2023 era.")
    # -------------------------------------------------------------

    # 5. THE LONGITUDINAL FUSION
    # We join on both ZIP and YEAR so 2018 stays with 2018, and 2023 with 2023.
    master_index = pd.merge(zip_equity, zip_behavior, on=['zip_code', 'survey_year'], how='inner')

    # --- NEW: STATISTICAL ROBUSTNESS CHECK ---
    # We define 'robust' as having at least 30 public observations AND 20 survey responses.
    # These thresholds are standard for 'Central Limit Theorem' assumptions.

    print("🛡️ Applying statistical robustness flags...")

    master_index = pd.merge(zip_equity, zip_behavior, on=['zip_code', 'survey_year'], how='inner')

    master_index['is_robust'] = (
            (master_index['public_total_stays'] >= 30) &
            (master_index['num_survey_respondents'] >= 20)
    )

    # 6. SAVE
    output_path = processed_path / "master_vitality_index.csv"
    master_index.to_csv(output_path, index=False)

    print(f"✅ Success! Master Index created at {output_path}")
    print(f"Final Dataset Shape: {master_index.shape}")

    # Quick Check of the DSR shift
    summary = master_index.groupby('survey_year')['public_dsr'].mean()
    print(f"\n📈 City-wide DSR Trend:\n{summary}")


if __name__ == "__main__":
    merge_vitality_data()