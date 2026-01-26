"""
FILE: 00_data_audit.py
PROJECT: Seattle Digital Equity & Public Life Study
DESCRIPTION: Performs a longitudinal audit of raw datasets. Validates sample sizes
             and schema integrity against minimum reliability thresholds (N=50).
OUTPUT: visualizations/raw_checks/audit_summary.png, data/processed/audit_results.json
"""

import logging
import pandas as pd
import matplotlib.pyplot as plt
import json
from pathlib import Path
from dsr_analysis import load_raw_counts

# 1. Configuration
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

current_file = Path(__file__).resolve()
BASE_DIR = current_file.parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "visualizations" / "raw_checks"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

MIN_N = 50
TARGET_YEARS = [2018, 2023]

def validate_schema():
    """Checks for required columns in primary datasets to prevent downstream crashes."""
    schema_map = {
        "staying.csv": ["staying_time_start", "staying_row_total", "location_id"],
        "locations.csv": ["location_id"]
    }

    for filename, cols in schema_map.items():
        path = RAW_DIR / filename
        if path.exists():
            df_head = pd.read_csv(path, nrows=1)
            missing = [c for c in cols if c not in df_head.columns]
            if missing:
                logger.warning(f"Schema Mismatch in {filename}: Missing {missing}")
                return False
    return True

def format_cell(val, year):
    """Formats table cells with Pass/Fail indicators for primary research years."""
    if not val or pd.isna(val) or val == 0:
        return "-"
    label = f"{int(val):,}"
    if year in TARGET_YEARS:
        return f"{label} [PASS]" if val >= MIN_N else f"{label} [FAIL]"
    return label

def main():
    logger.info("Starting Data Audit...")

    # 1. Integrity Checks
    if not validate_schema():
        logger.error("Data schema validation failed. Check raw CSV headers.")
        return

    # 2. Row Count Aggregation
    data_counts = load_raw_counts()
    years = list(range(2017, 2025))
    table_data = []
    audit_log = {"meta": {"min_n": MIN_N}, "results": {}}

    for y in years:
        counts = {
            "survey": data_counts["surveys"].get(y, 0),
            "staying": data_counts["staying"].get(y, 0),
            "moving": data_counts["moving"].get(y, 0)
        }

        audit_log["results"][y] = {
            "counts": counts,
            "status": "PASS" if (y not in TARGET_YEARS) or (counts["survey"] >= MIN_N and counts["staying"] >= MIN_N) else "FAIL"
        }

        table_data.append([
            str(y),
            format_cell(counts["survey"], y),
            format_cell(counts["staying"], y),
            format_cell(counts["moving"], y)
        ])

    # 3. Save Machine-Readable Artifact (The "Shablona" Move)
    with open(PROCESSED_DIR / "audit_results.json", "w") as f:
        json.dump(audit_log, f, indent=4)

    # 4. Visualization
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.axis('off')
    headers = ["Year", "Tech Survey (N)", "Public Staying (N)", "Public Moving (N)"]

    tbl = ax.table(
        cellText=table_data,
        colLabels=headers,
        loc='center',
        cellLoc='center',
        colColours=["#f2f2f2"] * 4
    )

    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1.2, 2.5)

    # Highlight target research years
    for (row, col), cell in tbl.get_celld().items():
        if row > 0:
            year_val = int(table_data[row-1][0])
            if year_val in TARGET_YEARS:
                cell.get_text().set_weight('bold')
                if audit_log["results"][year_val]["status"] == "FAIL":
                    cell.set_facecolor('#ffe6e6') # Light red for failures
                else:
                    cell.set_facecolor('#f0f9f0') # Light green for passes

    plt.title("Longitudinal Data Audit: Seattle Public Life & Digital Equity",
              fontsize=14, weight='bold', pad=30)

    plt.figtext(0.5, 0.05, f"Audit Logic: [PASS] requires N >= {MIN_N} for primary research years.",
                ha="center", fontsize=9, style='italic')

    save_path = OUTPUT_DIR / "audit_summary.png"
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    plt.close()

    logger.info(f"Audit complete. Summary saved to {save_path}")

if __name__ == "__main__":
    main()