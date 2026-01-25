"""
SPATIAL JOIN & CROSSWALK GENERATION
-----------------------------------
Purpose:
1. Converts WKT polygons from SDOT geography into centroids.
2. Performs a spatial 'point-in-polygon' join to assign each location_id
   to a Seattle ZIP code boundary.
3. Integrates manual patches for locations missing from the raw spatial data
   (e.g., PIK5, PIO19) to prevent observation data loss.

Output: data/processed/location_to_zip_crosswalk.csv
"""

import logging
import pandas as pd
import geopandas as gpd
from shapely import wkt
from pathlib import Path

# 1. Setup Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("spatial_join.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 2. Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"
processed_path = base_path / "data" / "processed"
processed_path.mkdir(parents=True, exist_ok=True)


def run_spatial_join():
    logger.info("Starting Spatial Join: Mapping Locations to ZIP Codes")

    try:
        # 3. Load Data
        geo_df = pd.read_csv(raw_path / "geography.csv")
        zips_gdf = gpd.read_file(raw_path / "seattle_zip_codes_trimmed.geojson")

        # Ensure the ZIP boundaries are in the standard WGS84 projection
        if zips_gdf.crs is None:
            zips_gdf.set_crs("EPSG:4326", inplace=True)
            logger.info("Coordinate Reference System (CRS) set to EPSG:4326")

        # 4. Generate Centroids
        # Convert WKT strings to geometry objects and find the center point
        geo_df['geometry'] = geo_df['polygon'].apply(wkt.loads)
        geo_df['centroid'] = geo_df['geometry'].apply(lambda x: x.centroid)

        gdf_centroids = gpd.GeoDataFrame(
            geo_df[['location_id', 'centroid']],
            geometry='centroid',
            crs="EPSG:4326"
        )
        logger.info(f"Generated centroids for {len(gdf_centroids)} study locations.")

        # 5. Spatial Join (Point-in-Polygon)
        # Predicate 'within' ensures the centroid point is inside the ZIP polygon
        joined = gpd.sjoin(gdf_centroids, zips_gdf, how="left", predicate="within")

        # Identify the ZIP code column (standard is 'zcta5ce10' or 'zipcode')
        zip_col_candidates = [c for c in joined.columns if 'zip' in c.lower() or 'zcta' in c.lower()]
        if not zip_col_candidates:
            logger.error("Could not identify ZIP code column in GeoJSON.")
            return

        target_col = zip_col_candidates[0]
        logger.info(f"Using column '{target_col}' as ZIP source.")

        # Create Crosswalk
        final_lookup = joined[['location_id', target_col]].copy()
        final_lookup.columns = ['location_id', 'zip_code']

        # 6. Apply Manual Patches (The 'Rescue' Mission)
        # These IDs were missing from geography.csv but have significant observation data.
        manual_patches = [
            {'location_id': 'BLT5', 'zip_code': '98121'},
            {'location_id': 'BLT6', 'zip_code': '98121'},  # Included based on project logic
            {'location_id': 'OTH3', 'zip_code': '98118'},
            {'location_id': 'PIK5', 'zip_code': '98122'},
            {'location_id': 'PIO19', 'zip_code': '98104'}
        ]
        patch_df = pd.DataFrame(manual_patches)

        # Remove any existing (null) entries for these IDs before appending patches
        final_lookup = final_lookup[~final_lookup['location_id'].isin(patch_df['location_id'])]
        final_lookup = pd.concat([final_lookup, patch_df], ignore_index=True)

        # 7. Data Cleaning & Normalization
        final_lookup['location_id'] = final_lookup['location_id'].astype(str)
        # Clean up floating point zip codes (e.g., '98101.0' -> '98101')
        final_lookup['zip_code'] = (final_lookup['zip_code']
                                    .astype(str)
                                    .str.replace(r'\.0$', '', regex=True)
                                    .str.strip())

        # Final Validation
        unmapped_count = final_lookup['zip_code'].isna().sum() or (final_lookup['zip_code'] == 'nan').sum()
        if unmapped_count > 0:
            logger.warning(f"Validation: {unmapped_count} locations failed to map to a ZIP code.")

        # 8. Save Artifact
        output_file = processed_path / "location_to_zip_crosswalk.csv"
        final_lookup.to_csv(output_file, index=False)

        logger.info(f"Crosswalk successfully created with {len(final_lookup)} locations.")
        logger.info(f"Final crosswalk saved to: {output_file}")

    except Exception as e:
        logger.exception(f"Critical failure during spatial join: {e}")


if __name__ == "__main__":
    run_spatial_join()