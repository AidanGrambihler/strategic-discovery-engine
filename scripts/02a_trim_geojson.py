import geopandas as gpd
import pandas as pd
from pathlib import Path

# Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"
processed_path = base_path / "data" / "processed"


def trim_geojson():
    print("✂️ Trimming massive GeoJSON... this might take a minute...")

    # 1. Load the big file (this is where the 194MB hits the RAM)
    big_map = gpd.read_file(raw_path / "seattle_zip_codes.geojson")

    # 2. Get the list of Seattle Zip Codes we actually care about
    df = pd.read_csv(processed_path / "master_vitality_index.csv")
    seattle_zips = df['zip_code'].unique().astype(str)

    # 3. Filter the Map
    # Ensure the GeoJSON key is lowercase
    trimmed_map = big_map[big_map['zcta5ce10'].isin(seattle_zips)]

    # 4. Save the new, tiny version
    output_path = raw_path / "seattle_zip_codes_trimmed.geojson"
    trimmed_map.to_file(output_path, driver='GeoJSON')

    print(f"✅ Done! New file size is significantly smaller.")
    print(f"📍 Original rows: {len(big_map)} | Trimmed rows: {len(trimmed_map)}")

if __name__ == "__main__":
    trim_geojson()