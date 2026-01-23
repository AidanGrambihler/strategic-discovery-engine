import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

# Setup Paths
base_path = Path(__file__).resolve().parent.parent
processed_path = base_path / "data" / "processed"
viz_path = base_path / "visualizations"
viz_path.mkdir(exist_ok=True)


def run_equity_eda():
    print("🎨 Generating Equity Baseline Visualizations...")

    # 1. LOAD DATA
    df = pd.read_csv(processed_path / "standardized_tech_surveys.csv")

    # Ensure zip_code is string for categorical plotting
    df['zip_code'] = df['zip_code'].astype(str).str.zfill(5)

    # 2. DATA AGGREGATION
    # We want to see the intersection of Income and Reliability
    equity_stats = df.groupby(['income_group', 'survey_year']).agg(
        avg_reliability=('reliability_score', 'mean'),
        total_respondents=('zip_respondent_count', 'count')
    ).reset_index()

    # 3. VISUAL 1: The Income-Reliability Gap
    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")

    # We use a pointplot to show the 'trajectory' across income levels
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
    plt.ylabel('Avg Reliability Score (1-5)', fontsize=12)
    plt.xlabel('Annual Household Income Group', fontsize=12)
    plt.xticks(rotation=45)
    plt.legend(title='Survey Year')

    plt.tight_layout()
    plt.savefig(viz_path / "income_reliability_gap.png", dpi=300)
    print(f"✅ Saved Income-Reliability Gap chart to {viz_path}")

    # 4. VISUAL 2: The "Need" Map (Zip-Level Heatmap)
    # This prepares the 'Need' side of your guiding question
    zip_reliability = df.groupby('zip_code')['reliability_score'].mean().sort_values()

    plt.figure(figsize=(10, 8))
    zip_reliability.plot(kind='barh', color='teal')
    plt.title('Average Internet Reliability by Seattle Zip Code', fontsize=14)
    plt.xlabel('Reliability Score (5 = Completely Adequate)')
    plt.axvline(x=df['reliability_score'].mean(), color='red', linestyle='--', label='City Average')
    plt.legend()

    plt.tight_layout()
    plt.savefig(viz_path / "zip_reliability_ranking.png", dpi=300)
    print(f"✅ Saved Zip-Level Reliability ranking to {viz_path}")


if __name__ == "__main__":
    run_equity_eda()