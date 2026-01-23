import pandas as pd
import geopandas as gpd
from shapely import wkt
from pathlib import Path

# 1. Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"
processed_path = base_path / "data" / "processed"
processed_path.mkdir(exist_ok=True)

# DOCUMENTATION: Manual Zip Code mapping for sites missing spatial metadata
# Logic: BLT = Belltown (Downtown Seattle), OTH = Other, PIK = Pike/Pine, PIO = Pioneer Square.
PATCH_MAP = {
    "BLT5": "98121",
    "OTH3": "98118",
    "PIK5": "98122",
    "PIO19": "98104"
}

try:
    # 2. Load Data
    print("📂 Loading study geography and zip code boundaries...")
    geo_df = pd.read_csv(raw_path / "geography.csv")

    # Load the GeoJSON you just downloaded
    zips_gdf = gpd.read_file(raw_path / "seattle_zip_codes.geojson")

    # 3. Apply your Centroid Logic
    # First, convert the SDOT WKT strings into actual objects
    geo_df['geometry'] = geo_df['polygon'].apply(wkt.loads)

    # Calculate the centroid of each study area (your specific approach)
    geo_df['centroid'] = geo_df['geometry'].apply(lambda x: x.centroid)

    # Create a GeoDataFrame using the centroids as the active mapping points
    gdf_centroids = gpd.GeoDataFrame(
        geo_df[['location_id', 'centroid']],
        geometry='centroid',
        crs="EPSG:4326"
    )

    # 4. Local Spatial Join
    # Instead of an API, we check which Seattle Zip boundary 'contains' each centroid
    print("🎯 Mapping centroids to Zip Codes...")
    joined = gpd.sjoin(gdf_centroids, zips_gdf, how="left", predicate="within")

    # 5. Extract Zip Code
    # The Seattle GeoJSON column name is usually 'zipcode' or 'ZCTA5CE10'
    # We'll use a flexible search to find it
    zip_col = [c for c in joined.columns if 'zip' in c.lower() or 'zcta' in c.lower()][0]

    final_lookup = joined[['location_id', zip_col]].copy()
    final_lookup.columns = ['location_id', 'zip_code']

    # 6. Append Manual Patches and Save
    # We use the string names to match the format of the spatial join results
    manual_rows = pd.DataFrame([
        {'location_id': 'BLT5', 'zip_code': '98121'},
        {'location_id': 'OTH3', 'zip_code': '98118'},
        {'location_id': 'PIK5', 'zip_code': '98122'},
        {'location_id': 'PIO19', 'zip_code': '98104'}
    ])

    # Combine them
    final_lookup = pd.concat([final_lookup, manual_rows], ignore_index=True)

    # Ensure everything is a string and clean up formatting
    final_lookup['location_id'] = final_lookup['location_id'].astype(str)
    final_lookup['zip_code'] = final_lookup['zip_code'].astype(str).str.replace('\.0$', '', regex=True)

    # Save the Crosswalk
    output_path = processed_path / "location_to_zip_crosswalk.csv"
    final_lookup.to_csv(output_path, index=False)

    print(f"✅ Success! Created crosswalk with {len(final_lookup)} locations.")
    print(f"📍 Patched rows added:\n{final_lookup.tail(5)}")

except Exception as e:
    print(f"❌ Error during spatial join: {e}")