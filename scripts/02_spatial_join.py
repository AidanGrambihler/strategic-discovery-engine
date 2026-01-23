import pandas as pd
import geopandas as gpd
from shapely import wkt
from pathlib import Path

# 1. Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"
processed_path = base_path / "data" / "processed"
processed_path.mkdir(exist_ok=True)

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

    # 6. Save the Crosswalk
    output_path = processed_path / "location_to_zip_crosswalk.csv"
    final_lookup.to_csv(output_path, index=False)

    print(f"✅ Success! Created crosswalk for {len(final_lookup)} locations.")
    print(f"📍 Sample Mapping:\n{final_lookup.head()}")

except Exception as e:
    print(f"❌ Error during spatial join: {e}")