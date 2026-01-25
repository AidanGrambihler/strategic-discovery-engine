"""
COMPREHENSIVE DIGITAL EQUITY & VITALITY EDA
-------------------------------------------
1. Spatial Equity: Reliability, Income, and Societal Impact heatmaps.
2. Longitudinal Change: Filtered Reliability Delta (2018 vs 2023).
3. Behavioral Rhythms: Temporal distribution of public space usage.
4. Socio-Digital Correlation: Relationship between demographics and DSR.
"""

import logging
import pandas as pd
import seaborn as sns
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.colors import TwoSlopeNorm
from matplotlib import patheffects

# 1. Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"
processed_path = base_path / "data" / "processed"

# Create a dedicated sub-folder for high-quality EDA visuals
viz_path = base_path / "visualizations" / "exploratory_analysis"
viz_path.mkdir(parents=True, exist_ok=True)

def load_data():
    seattle_map = gpd.read_file(raw_path / "seattle_zip_codes_trimmed.geojson")
    seattle_map = seattle_map.rename(columns={'zcta5ce10': 'zip_code'})
    seattle_map['zip_code'] = seattle_map['zip_code'].astype(str).str.zfill(5)

    df = pd.read_csv(processed_path / "master_vitality_index.csv")
    df['zip_code'] = df['zip_code'].astype(str).str.zfill(5)
    return seattle_map, df


def plot_spatial_heatmaps(seattle_map, df):
    # Standardized ranges based on your requirements
    metrics = {
        'res_pct_access': {
            'cmap': 'YlGn',  # Yellow to Green (Green = High Access)
            'title': 'Internet Access Penetration (%)',
            'vmin': 85.0, 'vmax': 100.0  # Standardizes the scale across eras
        },
        'res_avg_societal_impact': {
            'cmap': 'magma',
            'title': 'Tech Pessimism: Societal Impact',
            'vmin': 2.35, 'vmax': 2.75
        },
        'res_avg_locations_not_home': {
            'cmap': 'Purples',
            'title': 'Non-Home Digital Hub Dependency',
            'vmin': 1.6, 'vmax': 3.0
        },
        'res_avg_reliability': {
            'cmap': 'Blues',
            'title': 'Home Internet Quality',
            'vmin': 3.5, 'vmax': 4.5
        }
    }

    for col, settings in metrics.items():
        for year in [2018, 2023]:
            year_data = df[df['survey_year'] == year]
            merged = seattle_map.merge(year_data, on='zip_code', how='left')

            fig, ax = plt.subplots(1, 1, figsize=(10, 10))
            merged.plot(
                column=col,
                cmap=settings['cmap'],
                linewidth=0.5,
                ax=ax,
                edgecolor='0.5',
                legend=True,
                vmin=settings['vmin'],  # <--- Uniform Scale
                vmax=settings['vmax'],  # <--- Uniform Scale
                missing_kwds={'color': '#f0f0f0'}
            )

            for idx, row in merged.iterrows():
                # Get the center of the zip code polygon
                centroid = row['geometry'].representative_point().coords[:][0]

                # Draw the white text label
                txt = ax.text(
                    centroid[0], centroid[1],
                    s=row['zip_code'],
                    fontsize=7,
                    color='white',
                    ha='center',
                    fontweight='bold'
                )

                # Add a subtle black outline to make white text readable on light colors
                txt.set_path_effects([
                    patheffects.withStroke(linewidth=1.5, foreground='black', alpha=0.5)
                ])

            ax.set_title(f"{settings['title']} ({year})", fontsize=14)
            ax.set_axis_off()
            plt.savefig(viz_path / f"heatmap_{col}_{year}.png", dpi=300, bbox_inches='tight')
            plt.close()


def plot_temporal_patterns(df):
    """Bar chart showing city-wide distribution of stays across times of day with labels."""
    logger.info("Plotting standardized temporal usage patterns with data labels...")

    # Pre-aggregate counts to ensure year totals = 100%
    temp_df = df.groupby('survey_year')[
        ['obs_count_morning', 'obs_count_midday', 'obs_count_evening']].sum().reset_index()

    # Melt for plotting
    melted = temp_df.melt(id_vars=['survey_year'], var_name='Time of Day', value_name='Total_Count')

    # Calculate percentage within each year
    year_totals = melted.groupby('survey_year')['Total_Count'].transform('sum')
    melted['Percentage'] = (melted['Total_Count'] / year_totals) * 100

    # Clean labels for the X-axis
    melted['Time of Day'] = melted['Time of Day'].str.replace('obs_count_', '').str.capitalize()

    plt.figure(figsize=(10, 7))
    sns.set_style("whitegrid")  # Adds a clean background for readability

    ax = sns.barplot(
        data=melted,
        x='Time of Day',
        y='Percentage',
        hue='survey_year',
        palette='muted',
        errorbar=None  # Replaces ci=None for modern Seaborn versions
    )

    # --- ADD DATA LABELS ---
    # We iterate through the containers (groups of bars) created by Seaborn
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f%%', padding=3, fontsize=10, fontweight='bold')

    # Formatting
    plt.ylim(0, 100)
    plt.title("% of Staying Observations at Different Times of Day, by Year", fontsize=14, pad=20)
    plt.ylabel("Percentage of Annual Observations (%)")
    plt.xlabel("Time of Day")
    plt.legend(title="Observation Year", loc='upper right')

    # Save the chart
    plt.savefig(viz_path / "bar_temporal_rhythms_labeled.png", dpi=300, bbox_inches='tight')
    plt.close()

def plot_socio_digital_correlations(df):
    """Correlates Survey Demographics with Observational Behavior."""
    logger.info("Generating demographic-behavioral correlations...")

    # Example: Does a higher % of Asian or African American residents correlate with higher Public DSR?
    # Using Survey demographics (Ground Truth) vs Behavioral DSR
    demographics = ['res_pct_eth_asian', 'res_pct_eth_african_american', 'res_pct_eth_white', 'res_pct_gen_female']

    for demo in demographics:
        plt.figure(figsize=(10, 6))
        sns.regplot(data=df[df['is_robust']], x=demo, y='obs_dsr', scatter_kws={'alpha':0.5})
        plt.title(f"Correlation: {demo.replace('res_pct_', '').title()} % vs. Public DSR")
        plt.savefig(viz_path / f"corr_{demo}_vs_dsr.png", dpi=300)
        plt.close()

if __name__ == "__main__":
    s_map, master_df = load_data()

    plot_spatial_heatmaps(s_map, master_df)
    plot_temporal_patterns(master_df)
    plot_socio_digital_correlations(master_df)

    logger.info("EDA visual suite generation complete.")