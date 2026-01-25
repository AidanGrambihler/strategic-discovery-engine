"""
DATA AUDIT UTILITY
------------------
Purpose: Performs a year-by-year census of available observations across
all raw datasets (Tech Surveys, Staying, and Moving) from 2017 to 2024.

Output: Saves a summary table to visualizations/raw_checks/audit_summary.png
"""

import logging
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# 1. Setup Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_audit.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 2. Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"
output_path = base_path / "visualizations" / "raw_checks"
output_path.mkdir(parents=True, exist_ok=True)

# Threshold for visual indicators
MIN_N = 50

def get_survey_counts():
    """Returns a dictionary of survey counts for 2018 and 2023."""
    counts = {}
    for year in [2018, 2023]:
        file_path = raw_path / f"tech_survey_{year}.csv"
        try:
            df = pd.read_csv(file_path, low_memory=False)
            counts[year] = len(df)
            logger.info(f"Loaded Tech Survey {year}: {len(df):,} records found.")
        except FileNotFoundError:
            logger.warning(f"Tech Survey {year} not found at {file_path}")
            counts[year] = 0
    return counts

def get_observation_counts(filename, time_col):
    """Extracts year-by-year counts from Public Life datasets."""
    file_path = raw_path / filename
    try:
        df = pd.read_csv(file_path, low_memory=False)
        dt_format = "%Y %b %d %I:%M:%S %p"
        df['temp_year'] = pd.to_datetime(df[time_col], format=dt_format, errors='coerce').dt.year
        counts = df['temp_year'].value_counts().to_dict()
        logger.info(f"Successfully parsed {filename}.")
        return counts
    except FileNotFoundError:
        logger.error(f"Public Life file {filename} missing!")
        return {}

def format_cell(val, year):
    """Applies text-based pass/fail indicators to target years."""
    if val == 0 or pd.isna(val):
        return "-"
    formatted_val = f"{int(val):,}"
    if year in [2018, 2023]:
        indicator = " [PASS]" if val >= MIN_N else " [FAIL]"
        return formatted_val + indicator
    return formatted_val

def run_full_audit():
    logger.info("Starting Census of Raw Data Files (2017-2024)")

    # Gather Data
    survey_data = get_survey_counts()
    staying_data = get_observation_counts("staying.csv", "staying_time_start")
    moving_data = get_observation_counts("moving.csv", "moving_time_start")

    # Build Timeline Matrix
    years = list(range(2017, 2025))
    table_data = []

    for yr in years:
        table_data.append([
            str(yr),
            format_cell(survey_data.get(yr, 0), yr),
            format_cell(staying_data.get(yr, 0), yr),
            format_cell(moving_data.get(yr, 0), yr)
        ])

    # Render PNG Table
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.axis('off')
        header_labels = ["Year", "Tech Survey N", "Staying Obs N", "Moving Obs N"]
        table = ax.table(
            cellText=table_data,
            colLabels=header_labels,
            cellLoc='center',
            loc='center',
            colColours=["#f2f2f2"] * 4
        )
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1.2, 2.5)

        for (row, col), cell in table.get_celld().items():
            if row > 0:
                year_val = table_data[row-1][0]
                if year_val in ["2018", "2023"]:
                    cell.set_text_props(weight='bold')

        plt.title("Total Observations in Raw Data Files (2017-2024)", fontsize=14, weight='bold', pad=20)

        save_file = output_path / "audit_summary.png"
        plt.savefig(save_file, bbox_inches='tight', dpi=300)
        plt.close() # Important for memory in pipelines
        logger.info(f"Audit table successfully saved to {save_file}")

    except Exception as e:
        logger.error(f"Failed to generate audit visualization: {e}")

if __name__ == "__main__":
    run_full_audit()