"""
FILE: 06_eda_visualizations.py
PROJECT: Seattle Digital Equity & Public Life Study
DESCRIPTION: Generates production-quality geospatial heatmaps and behavioral charts.
             Includes a correlation matrix to audit for multicollinearity.
"""

import logging
import pandas as pd
import seaborn as sns
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path
from dsr_analysis import add_district_labels

# 1. Configuration
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("talk")

script_path = Path(__file__).resolve()
BASE_DIR = script_path.parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
VIZ_DIR = BASE_DIR / "visualizations" / "exploratory_analysis"
VIZ_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    """Loads standardized spatial and tabular data."""
    # Note: Using the standardized zip_code column from Script 02
    map_gdf = gpd.read_file(PROCESSED_DIR / "seattle_zip_codes_trimmed.geojson")
    df = pd.read_csv(PROCESSED_DIR / "master_table.csv")

    for item in [map_gdf, df]:
        item['zip_code'] = item['zip_code'].astype(str).str.zfill(5)

    return map_gdf, df

def plot_correlation_matrix(df):
    """Audits feature relationships to detect multicollinearity before modeling."""
    logger.info("Generating Correlation Matrix...")

    # Select key numerical variables for the regression
    features = [
        'res_avg_reliability', 'res_median_income',
        'res_pct_eth_african_american', 'res_pct_eth_asian',
        'obs_avg_temp', 'obs_dsr', 'obs_total_stays'
    ]

    corr = df[features].corr()

    plt.figure(figsize=(12, 10))
    sns.heatmap(corr, annot=True, cmap='RdBu_r', center=0, fmt='.2f', linewidths=0.5)
    plt.title("Feature Correlation Audit: Multicollinearity Check", pad=20, weight='bold')

    save_path = VIZ_DIR / "correlation_matrix.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

def plot_spatial_equity(map_gdf, df):
    """Generates longitudinal heatmaps with locked scales."""
    metrics = {
        'res_avg_reliability': ('Blues', 'Avg. Home Reliability (1-5)', (3.5, 4.5)),
        'res_median_income': ('Greens', 'Median Income ($)', (50000, 150000)),
        'obs_dsr': ('YlGnBu', 'Digital-to-Social Ratio (DSR)', (0.1, 0.6))
    }

    for col, (cmap, title, limits) in metrics.items():
        for year in [2018, 2023]:
            year_data = df[(df['survey_year'] == year) & (df['is_robust'])]
            merged = map_gdf.merge(year_data, on='zip_code', how='left')

            fig, ax = plt.subplots(1, 1, figsize=(10, 12))
            merged.plot(
                column=col, cmap=cmap, linewidth=0.5, ax=ax, edgecolor='0.2',
                legend=True, vmin=limits[0], vmax=limits[1],
                legend_kwds={'shrink': 0.6, 'label': title},
                missing_kwds={'color': '#f2f2f2', 'label': 'N < Threshold'}
            )

            add_district_labels(ax, merged, 'zip_code')
            ax.set_title(f"{title}\nSeattle, {year}", fontsize=16, pad=20, weight='bold')
            ax.set_axis_off()

            plt.savefig(VIZ_DIR / f"heatmap_{col}_{year}.png", dpi=300, bbox_inches='tight')
            plt.close()

def plot_observation_bias_check(df):
    """Validates temporal consistency across survey eras."""
    cols = ['obs_count_morning', 'obs_count_midday', 'obs_count_evening']
    temp = df.groupby('survey_year')[cols].sum().reset_index()
    melted = temp.melt(id_vars='survey_year', var_name='Period', value_name='Count')

    totals = melted.groupby('survey_year')['Count'].transform('sum')
    melted['Pct'] = (melted['Count'] / totals) * 100
    melted['Period'] = melted['Period'].str.split('_').str[-1].str.capitalize()

    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=melted, x='Period', y='Pct', hue='survey_year', palette='Blues')
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f%%', padding=3)

    plt.title("Study Consistency: Observation Windows", pad=20)
    plt.ylabel("Percentage of Total Observations (%)")
    plt.ylim(0, 100)
    plt.savefig(VIZ_DIR / "observation_temporal_bias_check.png", dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    logger.info("Generating EDA visual suite...")
    s_map, master_df = load_data()

    plot_correlation_matrix(master_df)
    plot_spatial_equity(s_map, master_df)
    plot_observation_bias_check(master_df)

    logger.info("EDA complete.")