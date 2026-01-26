"""
FILE: 07_statistical_modelling.py
PROJECT: Seattle Digital Equity & Public Life Study
DESCRIPTION: Causal inference suite. Includes Marginal Effects visualization
             to illustrate the impact of Income on Public Digital Life.
"""

import logging
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from statsmodels.iolib.summary2 import summary_col
from pathlib import Path

# Custom library imports
from dsr_analysis import (
    plot_coefficients,
    calculate_spatial_bias,
    calculate_vif
)

# 1. Setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
VIZ_DIR = BASE_DIR / "visualizations" / "final_analysis"
VIZ_DIR.mkdir(parents=True, exist_ok=True)

def plot_marginal_effects(model, model_df):
    """
    Visualizes the impact of Income while holding other variables at their mean.
    This provides the 'Hero Image' for the project's conclusions.
    """
    logger.info("Generating Marginal Effects Plot for Income...")

    # Create range for income
    income_range = np.linspace(model_df['res_median_income_z'].min(),
                               model_df['res_median_income_z'].max(), 100)

    # Reference dataframe (holding other variables constant)
    predict_df = pd.DataFrame({
        'res_median_income_z': income_range,
        'res_avg_reliability_z': 0,
        'res_pct_eth_african_american': model_df['res_pct_eth_african_american'].mean(),
        'res_pct_eth_asian': model_df['res_pct_eth_asian'].mean(),
        'obs_avg_temp_z': 0,
        'survey_year': model_df['survey_year'].mode()[0]
    })

    predictions = model.predict(predict_df)

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=model_df, x='res_median_income_z', y='obs_dsr',
                    alpha=0.4, color='gray', label='Observed ZIPs')

    plt.plot(income_range, predictions, color='#d95f02', linewidth=3,
             label='Mixed-Effects Marginal Trend')

    plt.title("The 'Income-Social' Gradient\nAs Income Increases, Public Digital-to-Social Ratios Drop",
              fontsize=14, weight='bold', pad=20)
    plt.xlabel("Median Income (Z-Scored)", fontsize=12)
    plt.ylabel("Digital-to-Social Ratio (DSR)", fontsize=12)
    plt.legend()

    plt.savefig(VIZ_DIR / "marginal_effects_income.png", dpi=300, bbox_inches='tight')
    plt.close()

# ... [Keep run_placebo_test and run_sensitivity_loo from previous versions] ...

def main():
    # --- 1. DATA PREPARATION ---
    df = pd.read_csv(PROCESSED_DIR / "master_table.csv")
    map_gdf = gpd.read_file(PROCESSED_DIR / "seattle_zip_codes_trimmed.geojson")

    for item in [map_gdf, df]:
        item['zip_code'] = item['zip_code'].astype(str).str.zfill(5)

    model_cols = ['obs_dsr', 'res_avg_reliability', 'res_median_income',
                  'res_pct_eth_african_american', 'res_pct_eth_asian',
                  'obs_avg_temp', 'survey_year', 'zip_code',
                  'obs_digital_users', 'obs_total_stays']

    model_df = df[df['is_robust']].copy().dropna(subset=model_cols).reset_index(drop=True)

    for col in ['res_avg_reliability', 'res_median_income', 'obs_avg_temp']:
        model_df[f'{col}_z'] = (model_df[col] - model_df[col].mean()) / model_df[col].std()

    # --- 2. THE MODEL STACK ---
    baseline_formula = ("obs_dsr ~ res_avg_reliability_z + res_median_income_z + "
                        "res_pct_eth_african_american + res_pct_eth_asian + "
                        "obs_avg_temp_z + C(survey_year)")

    m_ols = smf.ols(baseline_formula, data=model_df).fit()
    m_mixed = smf.mixedlm(baseline_formula, model_df, groups=model_df["zip_code"]).fit()

    # --- 3. EXPORT & VISUALIZE ---
    plot_marginal_effects(m_mixed, model_df)

    # ... [Keep previous diagnostics and summary_col exports] ...

    logger.info("Pipeline complete. Marginal effects plot saved.")

if __name__ == "__main__":
    main()