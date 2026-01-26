"""
dsr_analysis: A toolkit for investigating Digital-to-Social Ratios in urban spaces.
This package provides a standardized pipeline for processing SDOT Public Life 
observations and Seattle IT Digital Equity surveys.
"""

__version__ = "0.1.0"

# 1. Core Data Pipelines
# We expose the loader and clean_zip_code as they are essential for entry
from .data_loader import (
    load_raw_counts,
    clean_zip_code,
    get_usage_metrics,
    map_years_to_eras,
    load_master_table,
    load_seattle_geometry,
    get_survey_zip_codes,
    get_categorical_pcts,
    INCOME_LABELS_2018,
    INCOME_LABELS_2023,
    MIDPOINT_MAP_2018,
    MIDPOINT_MAP_2023
)

# 2. Spatial & GIS Utilities
from .spatial import (
    add_district_labels,
    calculate_spatial_autocorrelation, 
    plot_residuals,
    check_spatial_bridge,
    wkt_to_gdf
)

# 3. Statistical Modeling Stack
from .models import (
    calculate_vif,
    calculate_spatial_bias,
    plot_coefficients,
    run_placebo_test
)

# Explicitly define the public API
__all__ = [
    "load_raw_counts",
    "clean_zip_code",
    "get_usage_metrics",
    "map_years_to_eras",
    "add_district_labels",
    "calculate_spatial_autocorrelation",
    "plot_residuals",
    "calculate_vif",
    "calculate_spatial_bias",
    "plot_coefficients",
    "run_placebo_test"
]