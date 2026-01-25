"""
GEOJSON TRIMMING UTILITY
------------------------
Purpose: Filters a large municipal GeoJSON file to include only the ZIP codes
present in the Seattle Tech Access and Adoption surveys (2018 & 2023).

Note: This optimizes visualization performance by reducing file size and
ensuring spatial alignment with the survey study area.
"""

import logging
import pandas as pd
import geopandas as gpd
from pathlib import Path

# 1. Setup Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("geojson_trimming.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 2. Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"


def get_study_zip_codes():
    """Extracts unique ZIP codes from the raw survey files."""
    zips = set()
    survey_files = {
        "tech_survey_2018.csv": "qzip",
        "tech_survey_2023.csv": "ZIPCode"
    }

    for filename, col in survey_files.items():
        path = raw_path / filename
        if path.exists():
            df = pd.read_csv(path, usecols=[col], low_memory=False)
            unique_zips = df[col].dropna().unique().astype(str)
            zips.update(unique_zips)
            logger.info(f"Identified {len(unique_zips)} unique ZIPs from {filename}")
        else:
            logger.warning(f"Survey file missing during ZIP extraction: {filename}")

    return list(zips)


def trim_geojson():
    logger.info("Initializing GeoJSON trimming process")

    # 3. Load the Study Area ZIPs
    seattle_zips = get_study_zip_codes()
    if not seattle_zips:
        logger.error("No ZIP codes identified from surveys. Trimming aborted.")
        return

    # 4. Load the Big GeoJSON
    input_file = raw_path / "seattle_zip_codes.geojson"
    try:
        logger.info(f"Loading primary GeoJSON from {input_file}")
        big_map = gpd.read_file(input_file)

        # 5. Filter the Map
        # 'zcta5ce10' is the standard Census Bureau key for ZIP code polygons
        trimmed_map = big_map[big_map['zcta5ce10'].isin(seattle_zips)]

        # 6. Save Artifact
        output_file = raw_path / "seattle_zip_codes_trimmed.geojson"
        trimmed_map.to_file(output_file, driver='GeoJSON')

        logger.info("Trimming complete.")
        logger.info(f"Original polygons: {len(big_map)} | Retained: {len(trimmed_map)}")
        logger.info(f"Trimmed GeoJSON saved to: {output_file}")

    except FileNotFoundError:
        logger.critical(f"Input GeoJSON not found at {input_file}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    trim_geojson()