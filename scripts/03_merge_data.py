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
    zip_equity = df_survey.groupby(['zip_code', 'survey_year']).agg(
        num_survey_respondents=('zip_code', 'count'),
        avg_home_internet_reliability=('reliability_score', 'mean'),
        median_income_bracket=('income_score', 'median'),
        predominant_income_group=('income_group', lambda x: x.mode()[0] if not x.mode().empty else "Unknown"),
    ).reset_index()


    # ROUNDING: Keep the home reliability clean for display
    zip_equity['avg_home_internet_reliability'] = zip_equity['avg_home_internet_reliability'].round(2)

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

    # Aggregate behavioral metrics by Zip and Era
    # Note: 'survey_year' here now represents the lumped 2-year periods
    zip_behavior = staying_with_zips.groupby(['zip_code', 'survey_year']).agg(
        public_total_stays=('staying_row_total', 'sum'),
        digital_users=('using_electronics', 'sum'),
        social_users=('talking_to_others', 'sum')
    ).reset_index()

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