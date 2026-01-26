"""
FILE: 03_spatial_join.py
PROJECT: Seattle Digital Equity & Public Life Study
DESCRIPTION: Performs a Point-in-Polygon join to map study sites to ZIP codes.
             Applies manual patches to rescue orphaned high-traffic locations.
OUTPUT: data/processed/location_to_zip_crosswalk.csv
"""

import logging
import pandas as pd
import geopandas as gpd
from pathlib import Path
from dsr_analysis import wkt_to_gdf

# 1. Setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

script_path = Path(__file__).resolve()
BASE_DIR = script_path.parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Manual rescue patches (The "Expert Knowledge" layer)
GEOGRAPHIC_PATCHES = [
    {'location_id': 'BLT5', 'zip_code': '98121'},
    {'location_id': 'BLT6', 'zip_code': '98121'},
    {'location_id': 'OTH3', 'zip_code': '98118'},
    {'location_id': 'PIK5', 'zip_code': '98122'},
    {'location_id': 'PIO19', 'zip_code': '98104'}
]

def main():
    logger.info("Initializing Spatial Crosswalk Generation...")

    try:
        # 1. Load Data Assets
        geo_raw = pd.read_csv(RAW_DIR / "geography.csv")
        # Load the TRIMMED and STANDARDIZED map from Script 02
        zips_gdf = gpd.read_file(PROCESSED_DIR / "seattle_zip_codes_trimmed.geojson")

        # 2. Geometry Harmonization
        gdf_centroids = wkt_to_gdf(geo_raw)

        # 3. CRITICAL: CRS Alignment
        if gdf_centroids.crs != zips_gdf.crs:
            logger.info(f"Aligning CRS: Projecting centroids to {zips_gdf.crs}")
            gdf_centroids = gdf_centroids.to_crs(zips_gdf.crs)

        # 4. Spatial Join (Left join to keep all locations)
        # Note: 'zip_code' is already the name of the column thanks to Script 02
        joined = gpd.sjoin(gdf_centroids, zips_gdf[['zip_code', 'geometry']],
                           how="left", predicate="within")

        # 5. Extract Crosswalk and Audit Metadata
        crosswalk = joined[['location_id', 'zip_code']].copy()
        crosswalk['mapping_method'] = 'spatial_join'
        crosswalk.loc[crosswalk['zip_code'].isna(), 'mapping_method'] = 'unmapped'

        # 6. Apply 'Rescue' Logic (The "Patch" Move)
        # Convert patches to a indexed series for efficient updating
        patch_df = pd.DataFrame(GEOGRAPHIC_PATCHES)

        # Identify locations that need patching
        for _, patch in patch_df.iterrows():
            loc_id = patch['location_id']
            z_code = patch['zip_code']

            # If the loc_id exists, update it. If not, this script won't invent it.
            if loc_id in crosswalk['location_id'].values:
                crosswalk.loc[crosswalk['location_id'] == loc_id, 'zip_code'] = z_code
                crosswalk.loc[crosswalk['location_id'] == loc_id, 'mapping_method'] = 'manual_patch'

        # 7. Data Type Normalization
        # Force 5-digit strings and remove true orphans
        crosswalk = crosswalk.dropna(subset=['zip_code']).copy()
        crosswalk['zip_code'] = crosswalk['zip_code'].astype(str).str.split('.').str[0].str.zfill(5)

        # 8. Integrity Check
        orphan_count = len(gdf_centroids) - len(crosswalk)
        if orphan_count > 0:
            logger.warning(f"Spatial Gap: {orphan_count} locations could not be mapped (no polygon or patch).")

        # 9. Persistence
        output_file = PROCESSED_DIR / "location_to_zip_crosswalk.csv"
        crosswalk.to_csv(output_file, index=False)

        # Success Metrics
        patch_count = len(patch_df)
        logger.info(f"Mapped {len(crosswalk)} locations. (Used {patch_count} manual patches)")
        logger.info(f"Crosswalk saved: {output_file}")

    except Exception as e:
        logger.error(f"Spatial join workflow terminated: {e}")

if __name__ == "__main__":
    main()