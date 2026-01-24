import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
from pathlib import Path

# Path setup
base_path = Path(__file__).resolve().parent.parent
processed_path = base_path / "data" / "processed"


def run_advanced_models():
    df = pd.read_csv(processed_path / "master_vitality_index.csv")

    # Filter for robust data only
    model_df = df[df['is_robust'] == True].copy()

    print(f"📈 Modeling with {len(model_df)} robust neighborhood-year observations.")

    # --- MODEL 1: THE CORE SUBSTITUTION EFFECT ---
    # Does reliability predict DSR when we control for income and year?
    print("\n--- MODEL 1: Baseline ---")
    m1 = smf.ols('public_dsr ~ avg_home_internet_reliability + median_income_bracket + C(survey_year)',
                 data=model_df).fit()
    print(m1.summary())

    # --- MODEL 2: STRUCTURAL EQUITY CONTROLS ---
    # Adding residential demographics to ensure reliability isn't just a proxy for race/gender.
    print("\n--- MODEL 2: Structural Controls ---")
    m2_formula = """
        public_dsr ~ avg_home_internet_reliability + median_income_bracket + C(survey_year) + 
        pct_gen_female + pct_eth_african_american + pct_eth_hispanic
    """
    m2 = smf.ols(m2_formula, data=model_df).fit()
    print(m2.summary())

    # --- MODEL 3: THE "FULL CONTEXT" MODEL ---
    # Adding interaction (did the effect change?) + Weather + Observed Demographics.
    print("\n--- MODEL 3: Interaction & Environment ---")
    m3_formula = """
        public_dsr ~ avg_home_internet_reliability * C(survey_year) + 
        median_income_bracket + avg_staying_temperature + 
        obs_pct_gen_female + obs_pct_race_black
    """
    m3 = smf.ols(m3_formula, data=model_df).fit()
    print(m3.summary())


if __name__ == "__main__":
    run_advanced_models()