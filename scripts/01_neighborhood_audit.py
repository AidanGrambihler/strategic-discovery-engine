import pandas as pd
from pathlib import Path

# 1. Setup Robust Paths
# .resolve() ensures we have the full absolute path
# .parent.parent moves us from 'scripts/' up to the project root
base_path = Path(__file__).resolve().parent.parent
data_raw = base_path / "data" / "raw"

# Define file paths
locations_path = data_raw / "locations.csv"
geo_path = data_raw / "geography.csv"
tech_2018_path = data_raw / "tech_survey_2018.csv"
tech_2023_path = data_raw / "tech_survey_2023.csv"

try:
    # 2. Load the Data
    locations = pd.read_csv(locations_path)
    geo = pd.read_csv(geo_path)
    tech_2018 = pd.read_csv(tech_2018_path, low_memory=False)
    tech_2023 = pd.read_csv(tech_2023_path, low_memory=False)

    # 3. Identify Zip Code columns across both eras
    # We loop through both to see if the column names changed
    surveys = {"2018": tech_2018, "2023": tech_2023}
    for year, df in surveys.items():
        zip_matches = [c for c in df.columns if 'zip' in c.lower()]
        print(f"🔍 {year} Tech Survey Potential Zip Columns: {zip_matches}")

    # 4. The Spatial Bridge Strategy
    # We have WKT Polygons and 'locations_id' in 'geo' and 'locations_id' in 'locations'
    print("\n--- SPATIAL BRIDGE PREP ---")
    if 'polygon' in geo.columns:
        sample_wkt = str(geo['polygon'].iloc[0])[:60]
        print(f"✅ Geometry detected in 'polygon' column.")
        print(f"📍 Sample: {sample_wkt}...")
    else:
        print(f"❌ Error: 'polygon' column not found. Available: {geo.columns.tolist()}")

    # 5. Verify the Join Key (location_id)
        # Check if the IDs in 'locations.csv' exist in 'geography.csv'
    loc_ids = set(locations['location_id'].unique())
    geo_ids = set(geo['location_id'].unique())
    common_ids = loc_ids.intersection(geo_ids)

    print(f"\n--- ID ALIGNMENT CHECK ---")
    print(f"🔗 Locations with matching geography: {len(common_ids)} / {len(loc_ids)}")

    if len(common_ids) == 0:
        print("⚠️ Warning: No matching location_ids found between files! Check formatting.")
    else:
        print("✅ Ready for Spatial Join.")

except FileNotFoundError as e:
    print(f"❌ File not found! Check names: {e}")
except Exception as e:
    print(f"❌ Error: {e}")