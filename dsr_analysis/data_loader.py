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


def get_usage_metrics(row_or_df, year=None):
    """
    If passed a DataFrame, returns aggregate summary stats.
    If passed a Series (row), returns (locations_list, non_home_count).
    """
    # CASE 1: Processing a single survey row (Used in Script 04)
    if isinstance(row_or_df, pd.Series):
        # 2018 uses q11_1...q11_11 | 2023 uses Q11r1...Q11r11
        prefix = 'q11_' if year == 2018 else 'Q11r'
        # Check 11 possible locations (Home, Work, Library, etc.)
        cols = [f"{prefix}{i}" for i in range(1, 12)]

        active_locs = []
        for i, col in enumerate(cols, 1):
            if col in row_or_df and row_or_df[col] == 1:
                active_locs.append(i)

        # Count locations that are NOT Home (Index 1)
        non_home = len([loc for loc in active_locs if loc != 1])
        return "|".join(map(str, active_locs)), non_home

    # CASE 2: Aggregate metrics (Used elsewhere)
    df = row_or_df
    return {
        "total_observations": len(df),
        "avg_dsr": df['obs_dsr'].mean() if 'obs_dsr' in df.columns else None,
        "unique_zips": df['zip_code'].nunique() if 'zip_code' in df.columns else 0
    }


def map_years_to_eras(val):
    """
    Standardizes years into research buckets (2018 or 2023).
    Vectorized to handle single integers, Series, or DataFrames.
    """

    def logic(year):
        # Handle cases where year might be NaN
        if pd.isna(year):
            return np.nan
        return 2018 if year <= 2020 else 2023

    # CASE 1: It's a DataFrame
    if isinstance(val, pd.DataFrame):
        if 'survey_year' in val.columns:
            val['survey_year'] = val['survey_year'].apply(logic)
        return val

    # CASE 2: It's a Pandas Series (The fix for your current error)
    if isinstance(val, pd.Series):
        return val.apply(logic)

    # CASE 3: It's a single value (int or float)
    return logic(val)


def load_raw_counts(raw_dir=None):
    if raw_dir is None:
        # Get the absolute path of data_loader.py
        current_file = Path(__file__).resolve()

        # If your structure is: seattle-public-life-analysis/dsr_analysis/data_loader.py
        # Then .parent is dsr_analysis/
        # and .parent.parent is seattle-public-life-analysis/
        project_root = current_file.parent.parent

        # DEBUG PRINT: This will show up in your console so you can see the truth
        print(f"DEBUG: Project Root identified as: {project_root}")

        raw_dir = project_root / "data" / "raw"
    else:
        raw_dir = Path(raw_dir)

    years = [2018, 2023]

    # 1. Audit Surveys (Line counting is faster and safer than loading)
    survey_counts = {}
    for y in years:
        # Check for various naming conventions (tech_survey_2018.csv, etc.)
        possible_names = [f"tech_survey_{y}.csv", f"survey_{y}.csv", "tech_survey_cleaned.csv"]
        count = 0
        for name in possible_names:
            path = raw_dir / name
            if path.exists():
                with open(path, 'r') as f:
                    count = sum(1 for line in f) - 1
                break
        survey_counts[y] = count

    # 2. Helper to extract year counts from Public Life CSVs
    def get_yr_counts(file_name, col_name):
        path = raw_dir / file_name
        if not path.exists():
            logger.warning(f"Audit Target Missing: {path}")
            return {}

        try:
            df = pd.read_csv(path, usecols=[col_name], engine='c')

            # PROFESSIONAL FIX: Explicitly define the format to silence the warning
            # and ensure 100% accuracy in date parsing.
            SEATTLE_TIME_FORMAT = "%Y %b %d %I:%M:%S %p"
            dates = pd.to_datetime(
                df[col_name],
                format=SEATTLE_TIME_FORMAT,
                errors='coerce'
            )

            return dates.dt.year.dropna().astype(int).value_counts().to_dict()
        except Exception as e:
            logger.error(f"Failed to parse {file_name}: {e}")
            return {}

    # 3. Aggregate results
    # These keys (surveys, staying, moving) must match 00_data_audit.py
    return {
        "surveys": survey_counts,
        "staying": get_yr_counts("staying.csv", "staying_time_start"),
        "moving": get_yr_counts("moving.csv", "moving_time_start")
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


def get_survey_zip_codes(raw_dir):
    """
    Scans survey files to extract a unique list of ZIP codes.
    Robustly handles variations in column naming (e.g., 'Zip Code' vs 'zip_code').
    """
    raw_path = Path(raw_dir)
    years = [2018, 2023]
    unique_zips = set()

    for y in years:
        path = raw_path / f"tech_survey_{y}.csv"
        # Fallback to general cleaned file if specific year is missing
        if not path.exists():
            path = raw_path / "tech_survey_cleaned.csv"

        if path.exists():
            try:
                # Load the first few rows to find the right column name
                df_sample = pd.read_csv(path, nrows=1)

                # SHABLONA MOVE: Find the ZIP column regardless of case or spaces
                target_cols = ['zip_code', 'zip', 'zipcode', 'postal code', 'postal_code']
                zip_col = next((c for c in df_sample.columns
                                if c.lower().replace(' ', '_') in target_cols), None)

                if zip_col:
                    # Now load just that column
                    df = pd.read_csv(path, usecols=[zip_col])
                    cleaned = df[zip_col].apply(clean_zip_code).unique()
                    unique_zips.update(cleaned)
                    logger.info(f"Extracted {len(cleaned)} ZIPs from {path.name} using column '{zip_col}'")
                else:
                    logger.warning(f"No ZIP column found in {path.name}. Available: {list(df_sample.columns)}")

            except Exception as e:
                logger.warning(f"Could not extract ZIPs from {path}: {e}")

    unique_zips.discard("00000")
    return list(unique_zips)

def load_seattle_geometry(geo_path):
    """Loads GeoJSON and aligns ZIP code formatting for spatial joins."""
    gdf = gpd.read_file(geo_path)
    # Standardize column naming to 'zip_code' immediately
    if 'zcta5ce10' in gdf.columns:
        gdf = gdf.rename(columns={'zcta5ce10': 'zip_code'})

    gdf['zip_code'] = gdf['zip_code'].apply(clean_zip_code)
    return gdf