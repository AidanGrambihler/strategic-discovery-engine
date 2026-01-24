import pandas as pd
import seaborn as sns
import geopandas as gpd
import matplotlib.pyplot as plt
import folium
import json
import requests
from pathlib import Path
from pandas.api.types import CategoricalDtype

# Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"
processed_path = base_path / "data" / "processed"
viz_path = base_path / "visualizations"
viz_path.mkdir(exist_ok=True)


def run_equity_eda():
    print("🎨 Generating Equity Baseline Visualizations...")

    # 1. LOAD DATA
    # Use the Master Index so we benefit from the 'is_robust' flags
    df = pd.read_csv(processed_path / "master_vitality_index.csv")

    # We also need the raw standardized survey data for individual income plots
    df_survey = pd.read_csv(processed_path / "standardized_tech_surveys.csv")

    # --- THE FIX: Define logical income order ---
    income_order = [
        "Below $25-27k", "$25k-$49k", "$50k-$74k",
        "$75k-$99k", "$100k-$149k", "$150k-$199k", "$200k+"
    ]
    income_cat = CategoricalDtype(categories=income_order, ordered=True)
    df_survey['income_group'] = df_survey['income_group'].astype(income_cat)

    # 2. DATA AGGREGATION
    equity_stats = df_survey.groupby(['income_group', 'survey_year'], observed=False).agg(
        avg_reliability=('reliability_score', 'mean'),
        total_respondents=('zip_code', 'count')
    ).reset_index()

    # 3. VISUAL 1: The Income-Reliability Gap
    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")

    # Pointplot now respects the 'income_order'
    ax = sns.pointplot(
        data=equity_stats,
        x='income_group',
        y='avg_reliability',
        hue='survey_year',
        palette='viridis',
        markers=["o", "s"],
        linestyles=["-", "--"]
    )

    plt.title('Seattle Digital Equity: Home Internet Reliability by Income (2018 vs 2023)', fontsize=15, pad=20)
    plt.ylabel('Avg Reliability Score (5=Best, 1=Worst)', fontsize=12)
    plt.xlabel('Annual Household Income Group', fontsize=12)
    plt.xticks(rotation=45)
    plt.ylim(1, 5)  # Ensure we show the full scale
    plt.legend(title='Survey Year')

    plt.tight_layout()
    plt.savefig(viz_path / "income_reliability_gap.png", dpi=300)
    print(f"✅ Saved Sorted Income-Reliability Gap chart to {viz_path}")

    # 4. VISUAL 2: The "Need" Map (Zip-Level)
    # Filter for robust neighborhoods only for this ranking
    robust_zips = df[df['is_robust'] == True].groupby('zip_code')['avg_home_internet_reliability'].mean().sort_values()

    plt.figure(figsize=(10, 8))
    robust_zips.plot(kind='barh', color='teal')
    plt.title('Avg Internet Reliability by Zip (Robust Data Only)', fontsize=14)
    plt.xlabel('Reliability Score (5 = Completely Adequate)')

    # Add city average line
    city_avg = df_survey['reliability_score'].mean()
    plt.axvline(x=city_avg, color='red', linestyle='--', label=f'City Avg: {city_avg:.2f}')
    plt.legend()

    plt.tight_layout()
    plt.savefig(viz_path / "zip_reliability_ranking.png", dpi=300)
    print(f"✅ Saved Robust Zip-Level Reliability ranking to {viz_path}")

    # 3b. VISUAL 1b: Zoomed Income-Reliability Gap (Detail View)
    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")

    # Use the same pointplot logic
    sns.pointplot(
        data=equity_stats,
        x='income_group',
        y='avg_reliability',
        hue='survey_year',
        palette='magma',  # Switched to magma to distinguish it from the broad view
        markers=["o", "s"],
        linestyles=["-", "--"]
    )

    # THE CRITICAL CHANGE: Narrowing the window
    plt.ylim(3.5, 4.5)

    plt.title('Detail View: The Reliability Gap by Income (Zoomed 3.5-4.5)', fontsize=15, pad=20)
    plt.ylabel('Avg Reliability Score (Narrow Range)', fontsize=12)
    plt.xlabel('Annual Household Income Group', fontsize=12)

    # Adding an annotation to explain the zoom
    plt.annotate('Focusing on the 3.5-4.5 range to reveal subtle trends',
                 xy=(0.5, 3.55), xycoords='data', fontsize=10,
                 fontstyle='italic', color='gray')

    plt.xticks(rotation=45)
    plt.legend(title='Survey Year')

    plt.tight_layout()
    plt.savefig(viz_path / "income_reliability_gap_zoomed.png", dpi=300)
    print(f"🔍 Saved Zoomed Reliability Gap chart to {viz_path}")


def plot_static_equity_maps():
    print("🗺️ Generating Standardized Heatmaps (Scale: 3.8 - 4.4)...")

    seattle_map = gpd.read_file(raw_path / "seattle_zip_codes.geojson")
    df = pd.read_csv(processed_path / "master_vitality_index.csv")

    seattle_map = seattle_map.rename(columns={'zcta5ce10': 'zip_code'})
    seattle_map['zip_code'] = seattle_map['zip_code'].astype(int)

    # Define our standardized limits
    VMIN, VMAX = 3.8, 4.4

    for year in [2018, 2023]:
        year_data = df[df['survey_year'] == year]
        merged = seattle_map.merge(year_data, on='zip_code', how='left')

        fig, ax = plt.subplots(1, 1, figsize=(10, 12))

        # We use vmin and vmax to force the colorbar range
        merged.plot(
            column='avg_home_internet_reliability',
            cmap='RdYlGn',
            linewidth=1.2,
            ax=ax,
            edgecolor='black',
            legend=True,
            vmin=VMIN,  # Force the bottom of the scale
            vmax=VMAX,  # Force the top of the scale
            missing_kwds={'color': '#d1d1d1', 'label': 'No Data'},
            legend_kwds={
                'label': f"Avg Reliability Score ({VMIN} to {VMAX})",
                'orientation': "horizontal",
                'pad': 0.05,
                'shrink': 0.8
            }
        )

        # Zoom into Seattle boundaries
        ax.set_xlim(-122.45, -122.20)
        ax.set_ylim(47.45, 47.80)

        ax.set_title(f"Seattle Internet Reliability: {year}", fontsize=18, fontweight='bold')
        ax.annotate(f"Standardized Scale: {VMIN} (Red) to {VMAX} (Green)",
                    xy=(0.5, 0.02), xycoords='axes fraction', ha='center', fontsize=10, color='gray')

        ax.set_axis_off()

        plt.savefig(viz_path / f"standardized_map_reliability_{year}.png", dpi=300, bbox_inches='tight')
        print(f"✅ Saved standardized map for {year}.")

if __name__ == "__main__":
    run_equity_eda()
    plot_static_equity_maps()