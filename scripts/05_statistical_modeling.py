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
import libpysal
from esda.moran import Moran
from statsmodels.iolib.summary2 import summary_col

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
    # 1. Get parameters and confidence intervals based on model type
    if hasattr(model, 'fe_params'):
        params = model.fe_params
    else:
        params = model.params

    conf_int = model.conf_int()

    # 2. Filter out Intercept and Structural Variance (Group Var)
    to_drop = ['Intercept', 'Group Var']
    params = params.drop(labels=[idx for idx in to_drop if idx in params.index])
    conf_int = conf_int.drop(labels=[idx for idx in to_drop if idx in conf_int.index])

    # 3. Plotting
    plt.figure(figsize=(10, 6))

    # Calculate errors (n x 1 arrays)
    lower_err = params - conf_int[0]
    upper_err = conf_int[1] - params

    # Create the forest plot
    plt.errorbar(x=params, y=params.index, xerr=[lower_err, upper_err],
                 fmt='o', color='black', capsize=5)

    plt.axvline(x=0, color='red', linestyle='--', alpha=0.5)

    # Styling labels (Where fontweight actually works!)
    plt.title(f"Regression Coefficients: {name}", fontsize=14, fontweight='bold')
    plt.xlabel("Coefficient Estimate (Effect Size)", fontweight='bold')
    plt.yticks(fontweight='bold')

    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()

    plt.savefig(viz_path / f"model_forest_{name.lower().replace(' ', '_')}.png")
    plt.close()

def plot_residuals_map(model, model_df):
    """Visualizes where the model's predictions differ from reality."""
    logger.info("Generating Residuals Map...")

    # Load Geometry
    raw_path = base_path / "data" / "raw"
    seattle_map = gpd.read_file(raw_path / "seattle_zip_codes_trimmed.geojson")
    seattle_map = seattle_map.rename(columns={'zcta5ce10': 'zip_code'})
    seattle_map['zip_code'] = seattle_map['zip_code'].astype(str).str.zfill(5)

    # Prep DataFrame
    plot_df = model_df.copy()
    plot_df['zip_code'] = plot_df['zip_code'].astype(str).str.zfill(5)

    # Merge
    merged = seattle_map.merge(plot_df, on='zip_code', how='left')

    # Plot
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    div_norm = TwoSlopeNorm(vcenter=0)

    merged.plot(
        column='residuals',
        cmap='RdBu_r',
        norm=div_norm,
        legend=True,
        ax=ax,
        edgecolor='0.3',
        linewidth=0.5,
        missing_kwds={'color': '#f0f0f0', 'label': 'No Robust Data'}
    )

    for idx, row in merged.iterrows():
        if pd.notna(row['residuals']):
            centroid = row['geometry'].representative_point().coords[:][0]
            txt = ax.text(centroid[0], centroid[1], s=row['zip_code'],
                          fontsize=9, color='black', ha='center', fontweight='bold')
            txt.set_path_effects([patheffects.withStroke(linewidth=2, foreground='white')])

    ax.set_title("Seattle Digital Residuals: The 'Lifeboat' Outliers\n(Red: Higher than expected digital usage)", fontsize=16)
    ax.set_axis_off()
    plt.savefig(viz_path / "map_dsr_residuals.png", dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("Residuals map saved to visualizations folder.")

def run_placebo_test(model_df, features):
    logger.info("Conducting Causal Validation (Placebo Test)...")
    m_target = smf.ols(f"obs_dsr ~ {features}", data=model_df).fit()
    m_placebo = smf.ols(f"obs_total_stays ~ {features}", data=model_df).fit()

    print("\n" + "="*40 + "\nPLACEBO TEST: CAUSAL ROBUSTNESS\n" + "="*40)
    print(f"Target (DSR) Reliability P-value:  {m_target.pvalues['res_avg_reliability']:.4f}")
    print(f"Placebo (Total) Reliability P-value: {m_placebo.pvalues['res_avg_reliability']:.4f}")

    if m_target.pvalues['res_avg_reliability'] < 0.10 and m_placebo.pvalues['res_avg_reliability'] > 0.10:
        print("RESULT: SUCCESS. Evidence of a specific digital substitution effect.")
    else:
        print("RESULT: MIXED. Results suggest broader neighborhood patterns.")



def run_spatial_autocorrelation(model_df):
    logger.info("Running Global Moran's I on Residuals...")
    raw_path = base_path / "data" / "raw"
    seattle_map = gpd.read_file(raw_path / "seattle_zip_codes_trimmed.geojson")
    seattle_map = seattle_map.rename(columns={'zcta5ce10': 'zip_code'})

    # --- FIX: Force both to String and pad with zeros ---
    seattle_map['zip_code'] = seattle_map['zip_code'].astype(str).str.zfill(5)

    # Create a copy of the subset to avoid SettingWithCopy warnings
    subset_df = model_df[['zip_code', 'residuals']].copy()
    subset_df['zip_code'] = subset_df['zip_code'].astype(str).str.zfill(5)

    geo_df = seattle_map.merge(subset_df, on='zip_code').dropna(subset=['residuals'])

    # Create spatial weights
    w = libpysal.weights.Queen.from_dataframe(geo_df)
    w.transform = 'r'

    # Calculate Moran's I
    mi = Moran(geo_df['residuals'].values, w)

    print("\n" + "="*40 + "\nSPATIAL DIAGNOSTICS: MORAN'S I\n" + "="*40)
    print(f"Moran's I Statistic: {mi.I:.4f}")
    print(f"P-value:             {mi.p_sim:.4f}")
    print(f"Z-score:             {mi.z_sim:.4f}")
    print("RESULT: " + ("SPATIAL CLUSTERING" if mi.p_sim < 0.05 else "SPATIAL RANDOMNESS (SUCCESS)"))
    print("="*40)


def run_advanced_models():
    logger.info("Loading Master Vitality Index...")
    df = pd.read_csv(processed_path / "master_vitality_index.csv")
    model_df = df[df['is_robust'] == True].copy()

    model_df['res_pct_eth_other_combined'] = (
            model_df['res_pct_eth_mixed'] + model_df['res_pct_eth_other'] +
            model_df['res_pct_eth_ai_an'] + model_df['res_pct_eth_nh_pi']
    )

    # Models
    m3 = smf.ols(
        "obs_dsr ~ res_avg_reliability + res_pct_eth_african_american + res_pct_eth_other_combined + res_avg_locations_not_home + C(survey_year)",
        data=model_df).fit()
    m4 = smf.mixedlm("obs_dsr ~ res_avg_reliability + res_pct_eth_african_american + C(survey_year)", model_df,
                     groups=model_df["zip_code"]).fit()
    m5 = smf.ols(
        "obs_dsr ~ res_avg_reliability * res_median_income_bracket + res_pct_eth_african_american + C(survey_year)",
        data=model_df).fit()

    # Output summaries and plots
    for name, model in {"Model 3": m3, "Model 4": m4, "Model 5": m5}.items():
        print(f"\nSUMMARY FOR: {name}\n{model.summary()}")
        export_model_visual(model, name)

    # Attach residuals from our most robust model (m4) to the dataframe
    model_df['residuals'] = m4.resid.values

    # Run Validations
    best_features = "res_avg_reliability + res_pct_eth_african_american + C(survey_year)"
    run_placebo_test(model_df, best_features)
    plot_residuals_map(m4, model_df)
    run_spatial_autocorrelation(model_df)

    logger.info("All modeling and diagnostics complete.")

    # --- ITEM 1: THE STARGAZER-STYLE TABLE ---
    logger.info("Generating Side-by-Side Model Comparison...")

    # This creates a beautiful comparison table of your top 3 models
    comparison = summary_col(
        [m3, m4, m5],
        model_names=['Model 3 (OLS)', 'Model 4 (Mixed)', 'Model 5 (Interact)'],
        stars=True,
        float_format='%0.3f',
        info_dict={'N': lambda x: "{0:d}".format(int(x.nobs)),
                   'R2': lambda x: "{:.2f}".format(x.rsquared) if hasattr(x, 'rsquared') else "N/A"}
    )

    # Save the file
    with open(viz_path / "model_comparison_table.txt", "w") as f:
        f.write(comparison.as_text())

    print("\n" + "=" * 40 + "\nMODEL COMPARISON TABLE GENERATED\n" + "=" * 40)
    print(comparison)


if __name__ == "__main__":
    run_advanced_models()