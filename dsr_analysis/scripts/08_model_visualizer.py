import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import re
import logging
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration (Matches your project structure) ---
script_path = Path(__file__).resolve()
BASE_DIR = script_path.parents[2]

# Note: Using the specific path you provided
MODEL_SUMMARY_FILE = BASE_DIR / "visualizations" / "final_analysis" / "professional_model_summary.txt"

# Keep the output where it was, or you can move it to the same final_analysis folder
VISUALIZATION_OUTPUT_DIR = BASE_DIR / "visualizations" / "models"
VISUALIZATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_model_summary(file_path):
    logger.info(f"Parsing model summary from: {file_path}")
    with open(file_path, 'r') as f:
        content = f.read()

    # Define the models we are looking for
    model_names = ['OLS', 'MixedLM', 'NegBinom']
    data = []

    # Regex breakdown:
    # Group 1: The variable name (e.g., res_median_income_z)
    # Group 2-4: The coefficients with potential stars
    # Next Line: The standard errors in parentheses

    # This finds the term and the 3 coefficient values
    coeff_pattern = re.compile(r'^([\w\(\)\[\].:-]+)\s+([-]?[\d\.]+[\*]*)\s+([-]?[\d\.]+[\*]*)\s+([-]?[\d\.]+[\*]*)',
                               re.MULTILINE)
    # This finds the line immediately following with the 3 standard errors
    se_pattern = re.compile(r'^\s+\(([\d\.]+)\)\s+\(([\d\.]+)\)\s+\(([\d\.]+)\)', re.MULTILINE)

    matches = list(coeff_pattern.finditer(content))

    for match in matches:
        term = match.group(1)
        if term in ['OLS', 'MixedLM', 'NegBinom', 'Intercept']:  # Skip headers, keep Intercept
            if term != 'Intercept': continue

        coeffs = [match.group(2), match.group(3), match.group(4)]

        # Look for the SE line immediately after this match
        remaining_content = content[match.end():]
        se_match = se_pattern.search(remaining_content)

        if se_match:
            ses = [se_match.group(1), se_match.group(2), se_match.group(3)]

            for i, model in enumerate(model_names):
                c_str = coeffs[i]
                # Extract numeric part of coefficient
                val_match = re.match(r'([-]?[\d\.]+)', c_str)
                if val_match:
                    val = float(val_match.group(1))
                    stars = c_str.replace(val_match.group(1), '')

                    data.append({
                        'term': term,
                        'model': model,
                        'coefficient': val,
                        'std_error': float(ses[i]),
                        'significance': stars
                    })

    df = pd.DataFrame(data)
    if not df.empty:
        logger.info(f"Successfully parsed {len(df)} coefficient-model pairs.")
    return df


def plot_forest_plot(df, output_path):
    """
    Generates a forest plot of model coefficients and their confidence intervals.
    """
    if df.empty:
        logger.warning("Cannot plot forest plot: DataFrame is empty.")
        return

    unique_terms = df['term'].unique()
    unique_models = df['model'].unique()

    fig, ax = plt.subplots(figsize=(12, 0.6 * len(unique_terms) * len(unique_models)))
    y_positions = np.arange(len(unique_terms) * len(unique_models))

    # Define colors for models
    model_colors = {
        'OLS': '#1f77b4',  # Blue
        'MixedLM': '#ff7f0e',  # Orange
        'NegBinom': '#2ca02c'  # Green
    }

    # Define markers for significance
    sig_markers = {
        '': 'o',  # Not significant
        '*': '^',  # p < .1
        '**': 's',  # p < .05
        '***': 'D'  # p < .01
    }

    # Plot each coefficient
    for i, term in enumerate(unique_terms):
        for j, model in enumerate(unique_models):
            subset = df[(df['term'] == term) & (df['model'] == model)]

            if not subset.empty:
                row = subset.iloc[0]
                coeff = row['coefficient']
                se = row['std_error']
                significance = row['significance']

                # Calculate 95% Confidence Interval (approx 1.96 * SE)
                lower_ci = coeff - 1.96 * se
                upper_ci = coeff + 1.96 * se

                y_pos = y_positions[i * len(unique_models) + j]

                # Plot CI as a horizontal line
                ax.hlines(y_pos, lower_ci, upper_ci, color=model_colors[model], lw=2)
                # Plot coefficient as a point
                ax.plot(coeff, y_pos, marker=sig_markers.get(significance, 'o'),
                        color=model_colors[model], markersize=8, zorder=5,
                        label=f"{model} ({significance})" if i == 0 else "")  # Label once per model

    # Add a vertical line at 0 for reference
    ax.axvline(x=0, color='gray', linestyle='--', lw=1)

    # Set y-axis ticks and labels
    term_labels = []
    for i, term in enumerate(unique_terms):
        for j, model in enumerate(unique_models):
            model_label = f"{model}"
            term_labels.append(f"{term}\n({model_label})")

    ax.set_yticks(y_positions)
    ax.set_yticklabels(term_labels, fontsize=10)
    ax.tick_params(axis='x', labelsize=10)
    ax.set_xlabel("Coefficient Value", fontsize=12)
    ax.set_title("Model Coefficients and 95% Confidence Intervals", fontsize=14)

    # Create custom legend for models and significance
    legend_handles = []
    for model, color in model_colors.items():
        legend_handles.append(mpatches.Patch(color=color, label=model))

    for sig, marker in sig_markers.items():
        if sig:
            legend_handles.append(plt.Line2D([0], [0], color='black', marker=marker, linestyle='None',
                                             markersize=8, label=f"p{sig}"))

    # Place legend
    ax.legend(handles=legend_handles, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

    plt.tight_layout(rect=[0, 0, 0.85, 1])  # Adjust layout to make room for legend
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Forest plot saved to: {output_path}")


def main():
    if not MODEL_SUMMARY_FILE.exists():
        logger.error(f"Model summary file not found: {MODEL_SUMMARY_FILE}")
        logger.info("Please ensure 05_create_master_table.py (or your modeling script) has run successfully.")
        return

    df_coeffs = parse_model_summary(MODEL_SUMMARY_FILE)
    if df_coeffs.empty:
        logger.error("Failed to parse any coefficients from the summary file. Check format.")
        return

    output_plot_path = VISUALIZATION_OUTPUT_DIR / "model_coefficients_forest_plot.png"
    plot_forest_plot(df_coeffs, output_plot_path)


if __name__ == "__main__":
    main()