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

    # 2. AGGREGATE SURVEYS (The "Need" Context)
    zip_equity = df_survey.groupby(['zip_code', 'survey_year']).agg(
        avg_reliability=('reliability_score', 'mean'),
        primary_income_group=('income_group', lambda x: x.mode()[0] if not x.mode().empty else "Unknown"),
        zip_respondent_count=('zip_respondent_count', 'first')
    ).reset_index()

    # 3. PROCESS STAYING DATA (The "Behavior" Action)
    df_staying = pd.read_csv(raw_path / "staying.csv", low_memory=False)

    # Extract year to match the Survey eras
    df_staying['survey_year'] = pd.to_datetime(df_staying['staying_time_start']).dt.year

    # Filter only to our two target years
    df_staying = df_staying[df_staying['survey_year'].isin([2018, 2023])]

    # Merge with crosswalk to get zip codes
    staying_with_zips = pd.merge(df_staying, df_crosswalk, on='location_id', how='inner')

    # Aggregate behavioral metrics by Zip and Year
    zip_behavior = staying_with_zips.groupby(['zip_code', 'survey_year']).agg(
        total_stays=('staying_row_total', 'sum'),
        digital_users=('using_electronics', 'sum'),
        social_users=('talking_to_others', 'sum')
    ).reset_index()

    # 4. FEATURE ENGINEERING: Digital-to-Social Ratio (DSR)
    # Formula: Digital / (Social + 1) -> The +1 prevents DivisionByZero errors
    # A DSR > 1 means the space is primarily a 'Digital Utility'
    # A DSR < 1 means the space is primarily 'Social'
    print("🧪 Engineering the Digital-to-Social Ratio (DSR)...")
    zip_behavior['dsr'] = zip_behavior['digital_users'] / (zip_behavior['social_users'] + 1)

    # Also calculate % of population doing each for a normalized view
    zip_behavior['pct_digital'] = (zip_behavior['digital_users'] / zip_behavior['total_stays']) * 100

    # 5. THE LONGITUDINAL FUSION
    # We join on both ZIP and YEAR so 2018 stays with 2018, and 2023 with 2023.
    master_index = pd.merge(zip_equity, zip_behavior, on=['zip_code', 'survey_year'], how='inner')

    # 6. SAVE
    output_path = processed_path / "master_vitality_index.csv"
    master_index.to_csv(output_path, index=False)

    print(f"✅ Success! Master Index created at {output_path}")
    print(f"Final Dataset Shape: {master_index.shape}")

    # Quick Check of the DSR shift
    summary = master_index.groupby('survey_year')['dsr'].mean()
    print(f"\n📈 City-wide DSR Trend:\n{summary}")


if __name__ == "__main__":
    merge_vitality_data()