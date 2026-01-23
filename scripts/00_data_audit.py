import pandas as pd
from pathlib import Path

# Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"

# Configurable Threshold
MIN_SAMPLE_SIZE = 100


def audit_dataset(df, name, time_col):
    """Generically audits a dataframe for temporal sample size sufficiency."""
    print(f"\n--- 🔍 Auditing: {name} ---")

    # Extract Year
    df['temp_year'] = pd.to_datetime(df[time_col]).dt.year
    year_counts = df['temp_year'].value_counts().sort_index()

    # Print Counts
    print(f"Observations by Year:")
    print(year_counts)

    # Check 2018 and 2023
    for target_year in [2018, 2023]:
        n = year_counts.get(target_year, 0)
        status = "✅ SUFFICIENT" if n >= MIN_SAMPLE_SIZE else "❌ INSUFFICIENT"
        print(f"Year {target_year}: n={n} | {status}")

    return year_counts


def run_full_audit():
    print("🚀 Initializing Global Data Quality Audit...")

    # 1. Load Data
    try:
        df_staying = pd.read_csv(raw_path / "staying.csv", low_memory=False)
        df_moving = pd.read_csv(raw_path / "moving.csv", low_memory=False)
    except FileNotFoundError as e:
        print(f"🛑 Error: Could not find raw files. {e}")
        return

    # 2. Audit Both
    staying_stats = audit_dataset(df_staying, "STAYING.CSV (Behavior)", "staying_time_start")
    moving_stats = audit_dataset(df_moving, "MOVING.CSV (Flow)", "moving_time_start")

    # 3. Summary Decision Matrix
    print("\n--- ⚖️ Final Temporal Alignment Summary ---")

    can_align_staying = (staying_stats.get(2018, 0) >= MIN_SAMPLE_SIZE and
                         staying_stats.get(2023, 0) >= MIN_SAMPLE_SIZE)

    can_align_moving = (moving_stats.get(2018, 0) >= MIN_SAMPLE_SIZE and
                        moving_stats.get(2023, 0) >= MIN_SAMPLE_SIZE)

    print(f"Staying Data Ready for Longitudinal Analysis: {can_align_staying}")
    print(f"Moving Data Ready for Longitudinal Analysis: {can_align_moving}")


if __name__ == "__main__":
    run_full_audit()