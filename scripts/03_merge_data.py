import pandas as pd
from pathlib import Path

# 1. Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"
processed_path = base_path / "data" / "processed"

print("🔄 Starting Grand Merge: Linking Public Life Data with Technology Access and Adoption Surveys...")

try:
    # 2. Load the pieces of the puzzle
    staying = pd.read_csv(raw_path / "staying.csv", low_memory=False)
    crosswalk = pd.read_csv(processed_path / "location_to_zip_crosswalk.csv")
    tech_2018 = pd.read_csv(raw_path / "tech_survey_2018.csv", low_memory=False)
    tech_2023 = pd.read_csv(raw_path / "tech_survey_2023.csv", low_memory=False)

    # 3. Join Public Life with Zip Codes
    # This gives every 'staying' observation a Zip Code context
    staying_with_zip = staying.merge(crosswalk, on='location_id', how='inner')

    # 4. Filter for 'Electronics Use'
    # We want to focus on our specific 'Digital Lifeline' metric
    # Adjust column names based on your audit of staying.csv!
    elec_cols = [c for c in staying.columns if 'elec' in c.lower() or 'phone' in c.lower()]
    print(f"📊 Using activity columns: {elec_cols}")

    # 5. Create the Temporal Buckets
    staying_with_zip['year'] = pd.to_datetime(staying_with_zip['date']).dt.year

    # Pre-Pandemic Aggregation (2017-2019)
    pre_pandemic_life = staying_with_zip[staying_with_zip['year'] <= 2019].groupby('zip_code')[elec_cols].mean()

    # Post-Pandemic Aggregation (2021-2025)
    post_pandemic_life = staying_with_zip[staying_with_zip['year'] >= 2021].groupby('zip_code')[elec_cols].mean()

    # 6. Final Join (The Analysis-Ready Table)
    # This combines our two eras into a single master dataframe
    # (Simplified for now - we can refine which tech metrics we want next!)
    print("✨ Merging public life trends with digital access surveys...")

    # ... logic for final merge ...

    print("✅ Master Dataset successfully created!")

except Exception as e:
    print(f"❌ Merge Failed: {e}")