"""
NEIGHBORHOOD & SPATIAL ALIGNMENT AUDIT
--------------------------------------
Purpose: 
- Validates the 'Spatial Bridge' between site-level observations and GIS polygons.
- Quantifies data loss from missing spatial IDs.
"""

import logging
import pandas as pd
from pathlib import Path

# 1. Setup Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("neighborhood_audit.log"), # Saves a searchable artifact
        logging.StreamHandler()                       # Still outputs to console
    ]
)
logger = logging.getLogger(__name__)

# 2. Setup Robust Paths
base_path = Path(__file__).resolve().parent.parent
data_raw = base_path / "data" / "raw"

# Define file paths
locations_path = data_raw / "locations.csv"
geo_path = data_raw / "geography.csv"
staying_path = data_raw / "staying.csv"

def run_neighborhood_audit():
    logger.info("Initializing Neighborhood & Spatial Alignment Audit")

    try:
        # 3. Load the Data
        locations = pd.read_csv(locations_path)
        geo = pd.read_csv(geo_path)
        df_staying = pd.read_csv(staying_path, low_memory=False)

        # 4. Geometry Check
        if 'polygon' in geo.columns:
            logger.info("Geometry column validation: SUCCESS")
        else:
            logger.error("Geometry column validation: FAILED - 'polygon' not found.")
            return

        # 5. Verify the Join Key (location_id)
        loc_ids = set(locations['location_id'].unique())
        geo_ids = set(geo['location_id'].unique())
        common_ids = loc_ids.intersection(geo_ids)
        missing_ids = loc_ids - geo_ids

        logger.info(f"Alignment: {len(common_ids)} / {len(loc_ids)} sites mapped to geography.")

        # 6. Quantify Data Loss
        if missing_ids:
            logger.warning(f"Spatial Gap Detected: {len(missing_ids)} IDs missing polygons: {missing_ids}")

            impact_df = df_staying[df_staying['location_id'].astype(str).isin(missing_ids)]

            if not impact_df.empty:
                total_lost = len(impact_df)
                logger.warning(f"IMPACT: Spatial join will drop {total_lost} observations.")

                # Log detailed breakdown as a 'debug' or 'info' level
                breakdown = impact_df.groupby('location_id').size().to_dict()
                logger.info(f"Loss breakdown by site: {breakdown}")
            else:
                logger.info("Spatial Gap: No behavioral data tied to missing IDs. Risk is nominal.")
        else:
            logger.info("Spatial Bridge: 100% ID parity achieved.")

    except FileNotFoundError as e:
        logger.critical(f"Execution halted: File not found. {e}")
    except Exception as e:
        logger.exception("An unexpected error occurred during spatial audit.")

if __name__ == "__main__":
    run_neighborhood_audit()