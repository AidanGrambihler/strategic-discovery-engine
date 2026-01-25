"""
STATISTICAL MODELING
-----------------------------
"""

import logging
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import geopandas as gpd
from matplotlib.colors import TwoSlopeNorm
from matplotlib import patheffects

# 1. Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. Path Setup
base_path = Path(__file__).resolve().parent.parent
processed_path = base_path / "data" / "processed"
viz_path = base_path / "visualizations" / "final_analysis"
viz_path.mkdir(parents=True, exist_ok=True)

def export_model_visual(model, name):
    """Creates a forest plot of model coefficients."""
    params = model.params.drop('Intercept')
    conf_int = model.conf_int().drop('Intercept')

    plt.figure(figsize=(10, 6))
    errors = [params - conf_int[0], conf_int[1] - params]
    plt.errorbar(x=params, y=params.index, xerr=errors, fmt='o', color='black', capsize=5)
    plt.axvline(x=0, color='red', linestyle='--', alpha=0.5)
    plt.title(f"Regression Coefficients: {name}")
    plt.xlabel("Coefficient Estimate (Effect Size)")
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(viz_path / f"model_forest_{name.lower().replace(' ', '_')}.png")
    plt.close()


def plot_residuals_map(model, model_df):
    """Visualizes where the model's predictions differ from reality."""
    logger.info("Generating Residuals Map...")

    # 1. Attach residuals to the dataframe
    # Residual = Observed Value - Predicted Value
    model_df = model_df.copy()
    model_df['residuals'] = model.resid

    # 2. Load the Seattle Geometry
    # (Using the same path setup you have for other raw data)
    raw_path = base_path / "data" / "raw"
    seattle_map = gpd.read_file(raw_path / "seattle_zip_codes_trimmed.geojson")

    # Ensure ZIP codes are strings and formatted correctly for the merge
    seattle_map = seattle_map.rename(columns={'zcta5ce10': 'zip_code'})
    seattle_map['zip_code'] = seattle_map['zip_code'].astype(str).str.zfill(5)
    model_df['zip_code'] = model_df['zip_code'].astype(str).str.zfill(5)

    # 3. Merge data with geometry
    merged = seattle_map.merge(model_df, on='zip_code', how='left')

    # 4. Plotting
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))

    # Use 'TwoSlopeNorm' to ensure 0 (no error) is the center of the color scale
    # Red = Model under-predicted (High DSR), Blue = Model over-predicted (Low DSR)
    div_norm = TwoSlopeNorm(vcenter=0)

    merged.plot(
        column='residuals',
        cmap='RdBu_r',  # Red-Blue reversed so Red = High Residual
        norm=div_norm,
        legend=True,
        ax=ax,
        edgecolor='0.3',
        linewidth=0.5,
        missing_kwds={'color': '#f0f0f0', 'label': 'No Robust Data'}
    )

    # 5. Add ZIP Code labels for easy identification
    for idx, row in merged.iterrows():
        if pd.notna(row['residuals']):
            centroid = row['geometry'].representative_point().coords[:][0]
            txt = ax.text(centroid[0], centroid[1], s=row['zip_code'],
                          fontsize=9, color='black', ha='center', fontweight='bold')
            # Add a white outline to text for readability against the map
            txt.set_path_effects([patheffects.withStroke(linewidth=2, foreground='white')])

    ax.set_title("Seattle Digital Residuals: The 'Lifeboat' Outliers\n(Red: Higher than expected digital usage)",
                 fontsize=16)
    ax.set_axis_off()

    plt.savefig(viz_path / "map_dsr_residuals.png", dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("Residuals map saved to visualizations folder.")

def run_placebo_test(model_df, features):
    """
    Validation: Does Reliability predict 'Total Vitality' (Placebo)
    vs. 'Digital-to-Social Ratio' (Target)?
    """
    logger.info("Conducting Causal Validation (Placebo Test)...")

    # 1. Target Model (DSR)
    m_target = smf.ols(f"obs_dsr ~ {features}", data=model_df).fit()

    # 2. Placebo Model (Total People - should NOT be affected by internet quality)
    m_placebo = smf.ols(f"obs_total_stays ~ {features}", data=model_df).fit()

    print("\n" + "=" * 40)
    print("PLACEBO TEST: CAUSAL ROBUSTNESS")
    print("=" * 40)
    print(f"Target (DSR) Reliability P-value:  {m_target.pvalues['res_avg_reliability']:.4f}")
    print(f"Placebo (Total) Reliability P-value: {m_placebo.pvalues['res_avg_reliability']:.4f}")

    if m_target.pvalues['res_avg_reliability'] < 0.10 and m_placebo.pvalues['res_avg_reliability'] > 0.10:
        print("RESULT: SUCCESS. Evidence of a specific digital substitution effect.")
    else:
        print("RESULT: MIXED. Reliability may be a proxy for broader neighborhood vitality.")

def run_advanced_models():
    logger.info("Loading Master Vitality Index...")
    df = pd.read_csv(processed_path / "master_vitality_index.csv")

    # Filter for robust data
    model_df = df[df['is_robust'] == True].copy()

    # --- MODEL 1: THE CORE SUBSTITUTION EFFECT ---
    # Does poor reliability drive people to use more digital tools in public (DSR)?
    logger.info("Running Model 1: Substitution Effect")
    m1 = smf.ols('obs_dsr ~ res_avg_reliability + res_median_income_bracket + C(survey_year)',
                 data=model_df).fit()

    # --- MODEL 2: THE EQUITY CONTEXT ---
    # Adding demographics. We use 'res_pct_eth_white' as the reference point by omitting it,
    # or include specific minority percentages to see their unique dependency.
    logger.info("Running Model 2: Equity Context")

    # Create an "Other/Mixed" aggregate to use every piece of data without overfitting
    model_df['res_pct_eth_other_combined'] = (
            model_df['res_pct_eth_mixed'] +
            model_df['res_pct_eth_other'] +
            model_df['res_pct_eth_ai_an'] +
            model_df['res_pct_eth_nh_pi']
    )

    m2_formula = """
        obs_dsr ~ res_avg_reliability + 
                  res_pct_access +
                  res_avg_locations_not_home +
                  res_pct_eth_african_american +
                  res_pct_eth_hispanic +
                  res_pct_eth_asian +
                  res_pct_eth_other_combined +
                  res_pct_gen_female +
                  res_median_income_bracket +
                  obs_pct_time_morning + 
                  obs_pct_time_evening +
                  obs_avg_temp +
                  C(survey_year)
    """
    m2 = smf.ols(m2_formula, data=model_df).fit()

    # Model 3: The Optimized Equity Story
    m3_formula = """
        obs_dsr ~ res_avg_reliability + 
                  res_pct_eth_african_american + 
                  res_pct_eth_other_combined +
                  res_avg_locations_not_home +
                  C(survey_year)
    """
    m3 = smf.ols(m3_formula, data=model_df).fit()

    # Model 4: Mixed Effects (The Robust Verification)
    logger.info("Running Model 4: Mixed Effects Verification")

    m4_formula = "obs_dsr ~ res_avg_reliability + res_pct_eth_african_american + C(survey_year)"

    # We use 'groups=model_df["zip_code"]' to handle the neighborhood correlation
    m4 = smf.mixedlm(m4_formula, model_df, groups=model_df["zip_code"]).fit()

    # --- MODEL 5: THE INTERACTION MODEL (Complexity Boost) ---
    # Testing if the "Lifeboat" effect is stronger in certain income brackets
    logger.info("Running Model 5: Socio-Technical Interaction")
    m5_formula = "obs_dsr ~ res_avg_reliability * res_median_income_bracket + res_pct_eth_african_american + C(survey_year)"
    m5 = smf.ols(m5_formula, data=model_df).fit()

    # --- OUTPUT RESULTS ---
    models = {"Model 1 (Baseline)": m1, "Model 2 (Equity)": m2, "Model 3 (Optimized Equity)": m3, "Model 4 (Mixed Effects Verification)": m4, "Model 5 (Interaction Model)": m5}

    for name, model in models.items():
        print("\n" + "=" * 80)
        print(f" SUMMARY FOR: {name}")
        print("=" * 80)

        # Print the full summary (Good for checking R-squared and F-stat)
        print(model.summary())

        # Optional: Export the forest plot you already defined
        export_model_visual(model, name)

    best_features = "res_avg_reliability + res_pct_eth_african_american + C(survey_year)"
    # --- CALL THE PLACEBO TEST ---
    run_placebo_test(model_df, best_features)

    # Pass your most robust model (Model 4) and the dataframe
    plot_residuals_map(m4, model_df)

    logger.info("Statistical modeling and result printing complete.")

if __name__ == "__main__":
    run_advanced_models()