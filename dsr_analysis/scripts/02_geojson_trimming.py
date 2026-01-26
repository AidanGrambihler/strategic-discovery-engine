"""
FILE: 02_geojson_trimming.py
PROJECT: Seattle Digital Equity & Public Life Study
DESCRIPTION: Filters municipal GeoJSON to study area ZIP codes, heals invalid
             geometries, and ensures standardized projection (EPSG:4326).
"""

import logging
import geopandas as gpd
from pathlib import Path
from dsr_analysis import get_survey_zip_codes

# 1. Configuration
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

script_path = Path(__file__).resolve()
BASE_DIR = script_path.parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Define the standard projection for longitudinal consistency
# EPSG:4326 is WGS84 - standard for GPS and GeoJSON
TARGET_CRS = "EPSG:4326"

def main():
    logger.info("Initializing GeoJSON optimization and geometric healing...")

    # 1. Retrieve the 'Study Area' filter
    study_zips = [str(z).zfill(5) for z in get_survey_zip_codes(RAW_DIR)]
    if not study_zips:
        logger.error("No ZIP codes found in survey files. Aborting.")
        return

    # 2. Load the Master Geography
    input_path = RAW_DIR / "seattle_zip_codes.geojson"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    try:
        full_map = gpd.read_file(input_path)

        # 3. Handle Column Logic & Standardization
        # Census data often uses 'zcta5ce10'; Seattle Open Data often uses 'ZIPCODE'
        zip_col = next((c for c in ['zcta5ce10', 'ZIPCODE', 'ZIP', 'zip_code'] if c in full_map.columns), None)

        if not zip_col:
            logger.error(f"Could not find ZIP column in {full_map.columns}")
            return

        # Standardize column name for project-wide consistency
        full_map = full_map.rename(columns={zip_col: 'zip_code'})
        full_map['zip_code'] = full_map['zip_code'].astype(str).str.zfill(5)

        # 4. Perform Filter
        trimmed_map = full_map[full_map['zip_code'].isin(study_zips)].copy()

        # 5. Geometric Healing (The "Senior" DS Move)
        # Fixes self-intersections or invalid rings common in raw municipal files
        if not trimmed_map.is_valid.all():
            logger.info("Invalid geometries detected. Healing polygons...")
            trimmed_map['geometry'] = trimmed_map.geometry.make_valid()

        # 6. CRS Management
        if trimmed_map.crs is None:
            logger.warning("Input GeoJSON has no defined CRS. Assuming EPSG:4326.")
            trimmed_map.set_crs(TARGET_CRS, inplace=True)
        elif trimmed_map.crs != TARGET_CRS:
            logger.info(f"Re-projecting from {trimmed_map.crs} to {TARGET_CRS}")
            trimmed_map = trimmed_map.to_crs(TARGET_CRS)

        # 7. Metadata Pruning (Keep file size small)
        # We only need the zip_code and the geometry
        final_map = trimmed_map[['zip_code', 'geometry']]

        # 8. Persistence
        output_path = PROCESSED_DIR / "seattle_zip_codes_trimmed.geojson"
        final_map.to_file(output_path, driver='GeoJSON')

        logger.info(f"Success: Kept {len(final_map)} polygons. Map saved to {output_path}")

    except Exception as e:
        logger.error(f"Spatial processing failed: {e}")

if __name__ == "__main__":
    main()