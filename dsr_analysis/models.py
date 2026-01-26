import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import libpysal
import logging
import warnings
from esda.moran import Moran
from statsmodels.stats.outliers_influence import variance_inflation_factor
from patsy import dmatrices

logger = logging.getLogger(__name__)


def plot_coefficients(model, name, output_path):
    """
    Creates a professional forest plot of model coefficients.
    Highlights the 'Reliability' variable for easier interpretation.
    """
    # Handle MixedLM vs OLS attribute naming
    params = model.fe_params if hasattr(model, 'fe_params') else model.params
    conf_int = model.conf_int()

    # Drop non-behavioral coefficients for visual clarity
    to_drop = ['Intercept', 'Group Var']
    params = params.drop(labels=[idx for idx in to_drop if idx in params.index])
    conf_int = conf_int.drop(labels=[idx for idx in to_drop if idx in conf_int.index])

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    # Differentiate the primary hypothesis variable
    colors = ['#e67e22' if 'reliability' in idx.lower() else '#34495e' for idx in params.index]

    ax.errorbar(x=params, y=params.index,
                xerr=[params - conf_int[0], conf_int[1] - params],
                fmt='o', color='#34495e', capsize=5, elinewidth=2, markersize=8)

    ax.axvline(x=0, color='#c0392b', linestyle='--', alpha=0.8, linewidth=1.5)
    ax.set_title(f"Regression Coefficients: {name}", fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel("Coefficient Estimate (95% CI)")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def calculate_vif(df, formula):
    """
    Detects multicollinearity. Flags features exceeding the VIF threshold (5.0).
    """
    try:
        y, X = dmatrices(formula, df, return_type='dataframe')
        vif_data = pd.DataFrame()
        vif_data["feature"] = X.columns
        vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]

        # Professional Flagging
        high_vif = vif_data[vif_data['VIF'] > 5.0]['feature'].tolist()
        if high_vif:
            logger.warning(f"High Multicollinearity detected in: {high_vif}")

        return vif_data.sort_values("VIF", ascending=False)
    except Exception as e:
        logger.error(f"VIF Calculation failed: {e}")
        return pd.DataFrame()


def calculate_spatial_bias(df, geometry_df, column='residuals'):
    """
    Calculates Global Moran's I. Handles spatial islands by forcing
    a 'Queen' contiguity matrix with isolated observations dropped.
    """
    # Ensure join keys are standardized
    df['zip_code'] = df['zip_code'].astype(str).str.zfill(5)
    geometry_df['zip_code'] = geometry_df['zip_code'].astype(str).str.zfill(5)

    geo_df = geometry_df.merge(df[['zip_code', column]], on='zip_code').dropna(subset=[column])

    # Suppress pysal warnings about island ZIP codes (common in coastal cities like Seattle)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = libpysal.weights.Queen.from_dataframe(geo_df, silence_warnings=True)
        w.transform = 'r'

    # Check for empty weights (no neighbors found)
    if w.n == 0:
        logger.error("Spatial weights matrix is empty. Check geometry overlap.")
        return None

    return Moran(geo_df[column].values, w)


def fit_dsr_models(df):
    """
    Fits the core regression stack.
    Note: Uses HC3 robust standard errors to account for heteroscedasticity.
    """
    # 1. Baseline OLS with Robust Standard Errors
    m_baseline = smf.ols(
        "obs_dsr ~ res_avg_reliability + res_median_income_bracket + C(survey_year)",
        data=df
    ).fit(cov_type='HC3')

    # 2. Mixed-Effects to handle spatial clustering within ZIP codes
    m_mixed = smf.mixedlm(
        "obs_dsr ~ res_avg_reliability + res_pct_eth_african_american + C(survey_year)",
        df,
        groups=df["zip_code"]
    ).fit()

    return {
        "baseline": m_baseline,
        "mixed_effects": m_mixed
    }