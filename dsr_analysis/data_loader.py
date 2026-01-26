import pandas as pd
import geopandas as gpd
import numpy as np
import logging
from pathlib import Path

# Setup logging for the module
logger = logging.getLogger(__name__)

# --- Metadata Schemas (Kept in-file as requested) ---
RELIABILITY_DESC = {5: "Completely Adequate", 4: "Mostly Adequate", 3: "Sometimes Adequate", 2: "Rarely Adequate",
                    1: "Not Adequate"}
LOC_LEGEND = {1: "Home", 2: "Work", 3: "School", 4: "Library", 5: "Community Center", 6: "Religious/Cultural Center",
              7: "Friend/Relative Home", 8: "Public Plaza/Airport", 9: "Business/Coffee Shop", 10: "Other",
              11: "Do Not Use Internet", 12: "N/A"}

# 2018/2023 Survey Labels & Midpoints
INCOME_LABELS_2018 = {1: "Below $25k", 2: "$25k-$50k", 3: "$50k-$75k", 4: "$75k-$100k", 5: "$100k-$150k",
                      6: "$150k-$200k", 7: "$200k+"}
INCOME_LABELS_2023 = {1: "<$27k", 2: "$27k-$46k", 3: "$46k-$74k", 4: "$74k-$100k", 5: "$100k-$150k", 6: "$150k-$200k",
                      7: "$200k+"}

MIDPOINT_MAP_2018 = {1: 12500, 2: 37500, 3: 62500, 4: 87500, 5: 125000, 6: 175000, 7: 250000}
MIDPOINT_MAP_2023 = {1: 13500, 2: 36500, 3: 60000, 4: 87000, 5: 125000, 6: 175000, 7: 250000}


# --- Utility Functions ---

def clean_zip_code(z):
    """Standardizes ZIP codes to 5-digit strings. Handles floats and NaNs."""
    if pd.isna(z): return "00000"
    z_str = str(z).split('.')[0].replace(',', '').strip()
    return z_str.zfill(5) if z_str.isdigit() else "00000"


def get_categorical_pcts(df, group_col, prefix):
    """Computes normalized distribution percentages for categorical variables."""
    counts = pd.crosstab([df['zip_code'], df['survey_year']], df[group_col])
    pcts = (counts.div(counts.sum(axis=1), axis=0) * 100)
    # Ensure column names are 'clean' (lowercase, no spaces) for statsmodels formulas
    pcts.columns = [f"{prefix}_{str(c).lower().replace(' ', '_').replace('/', '_').replace('-', '_')}"
                    for c in pcts.columns]
    return pcts.reset_index()


def load_raw_counts(raw_dir):
    """
    Computes observation metadata.
    Optimized to avoid loading massive dataframes into memory just for counts.
    """
    raw_path = Path(raw_dir)
    years = [2018, 2023]
    DT_FORMAT = "%Y %b %d %I:%M:%S %p"

    survey_counts = {}
    for y in years:
        path = raw_path / f"tech_survey_{y}.csv"
        # Shablona Tip: Count rows without loading the whole file
        if path.exists():
            with open(path, 'r') as f:
                survey_counts[y] = sum(1 for line in f) - 1
        else:
            survey_counts[y] = 0

    # Define dtypes to avoid DtypeWarnings and save RAM
    staying = pd.read_csv(raw_path / "staying.csv", usecols=["staying_time_start"], engine='c')

    def get_yr_counts(df, col):
        return pd.to_datetime(df[col], format=DT_FORMAT, errors='coerce').dt.year.value_counts().to_dict()

    return {
        "surveys": survey_counts,
        "staying": get_yr_counts(staying, "staying_time_start")
    }


def load_master_table(processed_path):
    """
    Loads ABT, enforces types, and creates demographic aggregates.
    """
    df = pd.read_csv(processed_path)
    df = df[df['is_robust']].copy()
    df['zip_code'] = df['zip_code'].apply(clean_zip_code)

    # Shablona Strategy: Collapse small-N groups to increase statistical power
    minority_cols = ['res_pct_eth_mixed', 'res_pct_eth_other', 'res_pct_eth_ai_an', 'res_pct_eth_nh_pi']
    available = [c for c in minority_cols if c in df.columns]
    df['res_pct_eth_minority_combined'] = df[available].sum(axis=1)

    return df


def load_seattle_geometry(geo_path):
    """Loads GeoJSON and aligns ZIP code formatting for spatial joins."""
    gdf = gpd.read_file(geo_path)
    # Standardize column naming to 'zip_code' immediately
    if 'zcta5ce10' in gdf.columns:
        gdf = gdf.rename(columns={'zcta5ce10': 'zip_code'})

    gdf['zip_code'] = gdf['zip_code'].apply(clean_zip_code)
    return gdf