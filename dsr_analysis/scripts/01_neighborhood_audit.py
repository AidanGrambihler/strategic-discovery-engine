"""
FILE: 01_neighborhood_audit.py
PROJECT: Seattle Digital Equity & Public Life Study
DESCRIPTION: Validates the 'Spatial Bridge' between site-level observations
             and ZIP polygons. Quantifies data attrition and coordinate drift.
DEPENDENCIES: dsr_analysis, pandas
"""

import logging
import pandas as pd
from pathlib import Path
from dsr_analysis import check_spatial_bridge

# Standardize logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

current_file = Path(__file__).resolve()
BASE_DIR = current_file.parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"

# SEATTLE BOUNDARY CHECK (Rough bounding box for Seattle)
LAT_RANGE = (47.4, 47.8)
LON_RANGE = (-122.5, -122.2)

def audit_coordinate_integrity(df, name):
    """Validates if coordinates exist and fall within the expected Seattle region."""
    if 'latitude' in df.columns and 'longitude' in df.columns:
        # Check for nulls/zeros
        missing = df[(df['latitude'] == 0) | (df['longitude'] == 0) |
                     (df['latitude'].isna()) | (df['longitude'].isna())]

        # Check for 'Out of Bounds' (Common in data entry errors)
        out_of_bounds = df[~df['latitude'].between(*LAT_RANGE) |
                           ~df['longitude'].between(*LON_RANGE)].dropna(subset=['latitude', 'longitude'])

        if not missing.empty:
            logger.warning(f"QUALITY ALERT: {len(missing)} rows in {name} have null coordinates.")
        if not out_of_bounds.empty:
            logger.warning(f"SPATIAL DRIFT: {len(out_of_bounds)} rows in {name} are outside Seattle bounds.")

        if missing.empty and out_of_bounds.empty:
            logger.info(f"SUCCESS: {name} coordinates appear structurally sound and localized.")

def main():
    logger.info("Initializing Spatial Alignment Audit...")

    # Validate file existence before reading
    required = ["locations.csv", "geography.csv", "staying.csv"]
    if not all((RAW_DIR / f).exists() for f in required):
        logger.error("CRITICAL: Spatial source files missing from data/raw/")
        return

    # Load datasets
    locations = pd.read_csv(RAW_DIR / "locations.csv")
    geography = pd.read_csv(RAW_DIR / "geography.csv")
    staying = pd.read_csv(RAW_DIR / "staying.csv", low_memory=False)

    # 1. Coordinate Integrity Audit
    audit_coordinate_integrity(locations, "locations.csv")

    # 2. Schema Check
    if 'polygon' not in geography.columns:
        logger.error("SCHEMA ERROR: 'polygon' column missing. Spatial bridge is broken.")
        return

    # 3. ID Parity Analysis
    common_ids, missing_ids = check_spatial_bridge(locations, geography)
    match_rate = (len(common_ids) / len(locations)) * 100
    logger.info(f"Spatial Match Rate: {match_rate:.1f}% ({len(common_ids)} of {len(locations)} sites)")

    # 4. Impact Quantification (The 'Senior' Perspective)
    if missing_ids:
        lost_obs_df = staying[staying['location_id'].isin(missing_ids)]
        total_volume = staying['staying_row_total'].sum()
        lost_volume = lost_obs_df['staying_row_total'].sum()

        attrition_pct = (lost_volume / total_volume) * 100 if total_volume > 0 else 0

        logger.warning(f"ATTRITION RISK: {len(missing_ids)} Sites lack GIS polygons.")
        logger.warning(f"IMPACT: {lost_volume:,.0f} people ({attrition_pct:.1f}% of total volume) will be excluded.")

        if attrition_pct > 15:
            logger.error("HIGH ATTRITION: Loss exceeds 15% threshold. Results may be spatially biased.")

        # Human-readable summary
        name_col = next((c for c in ['site_name', 'location_name', 'study_area'] if c in locations.columns), None)
        if name_col:
            impacted = locations[locations['location_id'].isin(missing_ids)][name_col].unique()
            logger.info(f"Sample of Impacted Areas: {list(impacted)[:5]}")
    else:
        logger.info("SUCCESS: 100% spatial parity achieved.")

if __name__ == "__main__":
    main()