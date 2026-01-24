import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from pandas.api.types import CategoricalDtype

# Setup Paths
base_path = Path(__file__).resolve().parent.parent
raw_path = base_path / "data" / "raw"
viz_path = base_path / "visualizations" / "raw_checks"
viz_path.mkdir(parents=True, exist_ok=True)
processed_path = base_path / "data" / "processed"


def plot_combined_income_stacks():
    print("🎨 Generating Faceted Longitudinal Income Stacks...")
    df = pd.read_csv(processed_path / "standardized_tech_surveys.csv")

    # 1. Logic for "Breathing Room"
    # We split the Zips into groups of 6 so the charts aren't crowded
    all_zips = sorted(df['zip_code'].unique())
    zip_groups = [all_zips[i:i + 6] for i in range(0, len(all_zips), 6)]

    income_order = ["Below $25-27k", "$25k-$49k", "$50k-$74k", "$75k-$99k", "$100k-$149k", "$150k-$199k", "$200k+"]
    income_cat = CategoricalDtype(categories=income_order, ordered=True)
    df['income_group'] = df['income_group'].astype(income_cat)

    # 2. Create a "Grid" of plots
    fig, axes = plt.subplots(len(zip_groups), 1, figsize=(15, 5 * len(zip_groups)), sharey=True)

    for i, zips in enumerate(zip_groups):
        subset = df[df['zip_code'].isin(zips)]
        pivot_df = subset.groupby(['zip_code', 'survey_year', 'income_group'], observed=False).size().unstack(fill_value=0)

        pivot_df.plot(kind='bar', stacked=True, ax=axes[i], colormap='viridis_r', width=0.8, legend=False)
        axes[i].set_title(f"Socio-Economic Profile: Zips {zips[0]} to {zips[-1]}", fontsize=14)
        axes[i].set_xlabel("")
        axes[i].tick_params(axis='x', rotation=0) # No more neck-craning!

    # Add one shared legend at the top
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=4, bbox_to_anchor=(0.5, 0.98))

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(viz_path / "raw_income_faceted_comparison.png")

def plot_demographic_stratification():
    """Establish the 'Need' by correlating income and reliability."""
    print("📊 Establishing Socio-Technical Baseline...")
    df = pd.read_csv(processed_path / "standardized_tech_surveys.csv")

    # 1. Correlation Matrix Preparation
    # We convert categories to codes to see the statistical relationship
    df_corr = df.copy()
    df_corr['income_code'] = df_corr['income_group'].astype('category').cat.codes
    df_corr['eth_code'] = df_corr['ethnicity_group'].astype('category').cat.codes

    # Focus on 2023 for the most current 'Vulnerability' snapshot
    df_2023 = df_corr[df_corr['survey_year'] == 2023]

    # Create a pivot table for a heatmap: Income vs Ethnicity vs Reliability
    pivot_table = df_2023.pivot_table(
        values='reliability_score',
        index='income_group',
        columns='ethnicity_group',
        aggfunc='mean'
    )

    plt.figure(figsize=(14, 8))
    sns.heatmap(pivot_table, annot=True, cmap='RdYlGn', fmt=".2f", cbar_kws={'label': 'Avg Reliability (5=Best)'})
    plt.title("Socio-Technical Vulnerability Heatmap (2023)\nAverage Home Internet Reliability by Income & Ethnicity",
              fontsize=15)
    plt.tight_layout()
    plt.savefig(viz_path / "equity_vulnerability_heatmap.png")


def generate_vulnerability_ranking():
    """Identify 'Digital Deserts' by ranking Zips by reliability gap."""
    print("🗺️ Identifying Digital Deserts...")
    df = pd.read_csv(processed_path / "standardized_tech_surveys.csv")

    # Calculate City-Wide Mean
    city_mean = df['reliability_score'].mean()

    # Aggregate by Zip
    zip_needs = df.groupby('zip_code').agg(
        avg_reliability=('reliability_score', 'mean'),
        sample_size=('zip_code', 'count')
    ).reset_index()

    # Calculate 'Vulnerability Score' (Distance from City Mean)
    zip_needs['vulnerability_index'] = city_mean - zip_needs['avg_reliability']
    zip_needs = zip_needs.sort_values('vulnerability_index', ascending=False)

    # Plot the Deserts
    plt.figure(figsize=(10, 12))
    colors = ['crimson' if x > 0 else 'seagreen' for x in zip_needs['vulnerability_index']]
    sns.barplot(data=zip_needs, y='zip_code', x='vulnerability_index', palette=colors)

    plt.axvline(0, color='black', linewidth=1)
    plt.title("Seattle Digital Desert Ranking\n(Positive = Below City Average Reliability)", fontsize=14)
    plt.xlabel("Vulnerability Score (Distance from City Mean)")
    plt.tight_layout()
    plt.savefig(viz_path / "digital_desert_ranking.png")


def audit_raw_reliability():
    """Visualize the confusing raw scale before we inverted it."""
    print("📊 Auditing Raw Reliability Scales...")
    df_18 = pd.read_csv(raw_path / "tech_survey_2018.csv")
    df_23 = pd.read_csv(raw_path / "tech_survey_2023.csv")

    # Calculate the global maximum Y-limit
    # This finds the highest frequency in either dataset to synchronize the scale
    max_18 = df_18['q6'].value_counts().max()
    max_23 = df_23['Q6'].value_counts().max()
    global_max = max(max_18, max_23) * 1.05  # Add 5% padding for labels

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # 2018 Plot (Notice the 0, 8, 9 codes)
    sns.countplot(data=df_18, x='q6', ax=axes[0], palette='magma')
    axes[0].set_title("Raw 2018 Reliability Codes (q6)\nIncludes 0, 8, 9")
    axes[0].set_ylim(0, global_max)

    # 2023 Plot (Notice the 1-7 scale)
    sns.countplot(data=df_23, x='Q6', ax=axes[1], palette='viridis')
    axes[1].set_title("Raw 2023 Reliability Codes (Q6)\nIncludes 6, 7")
    axes[1].set_ylim(0, global_max)

    plt.tight_layout()
    plt.savefig(viz_path / "raw_reliability_comparison.png")


def audit_moving_vs_staying_volume():
    """Compare the raw record counts of Staying vs Moving across years."""
    print("📊 Auditing Moving vs Staying Observation Volumes...")

    # Load raw datasets
    df_staying = pd.read_csv(raw_path / "staying.csv", low_memory=False)
    df_moving = pd.read_csv(raw_path / "moving.csv", low_memory=False)

    # Extract years
    df_staying['year'] = pd.to_datetime(df_staying['staying_time_start']).dt.year
    df_moving['year'] = pd.to_datetime(df_moving['moving_time_start']).dt.year

    # Create a comparison dataframe
    stay_counts = df_staying['year'].value_counts().sort_index().reset_index()
    stay_counts.columns = ['year', 'count']
    stay_counts['type'] = 'Staying'

    move_counts = df_moving['year'].value_counts().sort_index().reset_index()
    move_counts.columns = ['year', 'count']
    move_counts['type'] = 'Moving'

    comparison_df = pd.concat([stay_counts, move_counts])

    # Plot
    plt.figure(figsize=(12, 6))
    sns.barplot(data=comparison_df, x='year', y='count', hue='type')
    plt.title("Comparison of Raw Observation Volumes: Moving vs. Staying")
    plt.ylabel("Number of Row Records")
    plt.yscale('log')  # Using log scale if the difference in volume is massive

    plt.savefig(viz_path / "raw_behavior_volume_comparison.png")


if __name__ == "__main__":
    sns.set_theme(style="whitegrid")
    plot_combined_income_stacks()
    plot_demographic_stratification
    generate_vulnerability_ranking
    audit_raw_reliability()
    audit_moving_vs_staying_volume()
    print(f"✅ Raw Audit Visuals saved to {viz_path}")