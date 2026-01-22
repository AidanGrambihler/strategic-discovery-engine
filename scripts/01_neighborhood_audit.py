import pandas as pd
from pathlib import Path

# 1. Setup Robust Paths
# .resolve() ensures we have the full absolute path
# .parent.parent moves us from 'scripts/' up to the project root
base_path = Path(__file__).resolve().parent.parent

# Define file paths
locations_path = base_path / "data" / "raw" / "locations.csv"
tech_path = base_path / "data" / "raw" / "tech_survey.csv"

try:
    # 2. Load the Data
    locations = pd.read_csv(locations_path)
    tech_survey = pd.read_csv(tech_path)

    print(f"✅ Successfully loaded {len(locations)} rows from {locations_path.name}")
    print(f"✅ Successfully loaded {len(tech_survey)} rows from {tech_path.name}")
    print("-" * 30)

    # 3. Audit Neighborhood Names in 'Locations'
    # We know 'neighborhood' exists here based on SDOT documentation
    public_life_hoods = sorted(locations['location_neighborhood'].unique().tolist())
    print(f"Public Life Neighborhoods ({len(public_life_hoods)}):")
    print(public_life_hoods)
    print("-" * 30)

    # 4. Audit 'Tech Survey' Columns
    # We need to find the column that matches neighborhoods
    print("Columns in Tech Survey (looking for the 'Bridge' column):")
    for col in tech_survey.columns:
        # This highlights columns that likely contain geographic data
        if any(key in col.lower() for key in ['hood', 'area', 'district', 'puma', 'zip']):
            print(f"🔍 POTENTIAL MATCH: {col}")
        else:
            print(f"  {col}")

except FileNotFoundError as e:
    print(f"❌ File not found! Check your folder structure: {e}")
except Exception as e:
    print(f"❌ An error occurred: {e}")

# 5. Documenting the Join Key Mismatch
# ---------------------------------------------------------
print("\n--- JOIN KEY MISMATCH ANALYSIS ---")

# Identify the specific column we found for Zip Codes
# (Assuming the column is named 'Zip_Code' or similar)
tech_zip_col = 'Zip_Code'  # Update this if the name is slightly different!

print(f"Observation: Tech Survey uses '{tech_zip_col}' while Public Life uses 'location_neighborhood'.")
print(f"Action: A 'Crosswalk' or 'Spatial Join' is required to link these datasets.")

# Let's see the unique Zip Codes we are working with
available_zips = sorted(tech_survey[tech_zip_col].dropna().unique().tolist())
print(f"\nUnique Zip Codes in Tech Survey ({len(available_zips)} total):")
print(available_zips)

# Check if Public Life has ANY hidden Zip info
potential_geo_cols = [c for c in locations.columns if 'zip' in c.lower() or 'address' in c.lower()]
print(f"\nChecking Locations for hidden bridge columns: {potential_geo_cols}")