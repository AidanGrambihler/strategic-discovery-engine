import pandas as pd
import numpy as np
import statsmodels.api as sm
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

# Setup Paths
base_path = Path(__file__).resolve().parent.parent
processed_path = base_path / "data" / "processed"
viz_path = base_path / "visualizations" / "models"
viz_path.mkdir(parents=True, exist_ok=True)


def run_dsr_model():
    print("🧪 Running Multivariate Regression: Testing the 'Lifeboat' Theory...")

    # 1. LOAD DATA
    df = pd.read_csv(processed_path / "master_vitality_index.csv")

    # Filter for Robust neighborhoods to avoid noise
    # We also ensure we have the necessary columns
    model_df = df[df['is_robust'] == True].copy()

    # Calculate DSR (Digital-to-Social Ratio)
    # Using +1 to avoid infinity, though robust zips should have social users
    model_df['dsr'] = model_df['digital_users'] / (model_df['social_users'] + 1)

    # 2. RUN MODELS BY ERA (2018 vs 2023)
    # This addresses your second question: "Have trends shifted post-pandemic?"
    for year in [2018, 2023]:
        print(f"\n--- {year} ERA ANALYSIS ---")
        era_data = model_df[model_df['survey_year'] == year].dropna(
            subset=['avg_home_internet_reliability', 'median_income_bracket', 'dsr'])

        if era_data.empty:
            print(f"⚠️ No robust data for {year}. Skipping...")
            continue

        # Independent Variables: Reliability + Income (The "Double Check")
        X = era_data[['avg_home_internet_reliability', 'median_income_bracket']]
        X = sm.add_constant(X)  # Add the Intercept
        y = era_data['dsr']

        model = sm.OLS(y, X).fit()
        print(model.summary())

        # 3. VISUAL: The "Proof" Plot
        # We plot the relationship while controlling for income visually using hue
        plt.figure(figsize=(10, 6))
        sns.scatterplot(
            data=era_data,
            x='avg_home_internet_reliability',
            y='dsr',
            size='num_survey_respondents',
            palette='viridis',
            sizes=(50, 400)
        )

        # Add a regression line for the overall era trend
        sns.regplot(data=era_data, x='avg_home_internet_reliability', y='dsr', scatter=False, color='red',
                    label='Era Trend')

        plt.title(f"{year} Digital Lifeboat: Reliability vs. DSR\n(Controlled for Income)", fontsize=14)
        plt.xlabel("Avg Home Internet Reliability (5 = High)")
        plt.ylabel("Public Digital-to-Social Ratio (DSR)")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(viz_path / f"dsr_model_plot_{year}.png")


if __name__ == "__main__":
    sns.set_theme(style="whitegrid")
    run_dsr_model()