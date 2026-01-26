import logging
import warnings
import matplotlib.pyplot as plt
import geopandas as gpd
import libpysal
from esda.moran import Moran
from matplotlib.colors import TwoSlopeNorm
from matplotlib import patheffects
from shapely import wkt

logger = logging.getLogger(__name__)

# Seattle-specific projection (UTM Zone 10N) for metric accuracy
SEATTLE_CRS = "EPSG:32610"


def wkt_to_gdf(df, wkt_col='polygon', crs="EPSG:4326"):
    """
    Converts a DataFrame with a WKT column into a GeoDataFrame.
    Handles Point, Polygon, and MultiPolygon strings.
    """
    if wkt_col not in df.columns:
        raise KeyError(f"Column '{wkt_col}' not found in DataFrame. Available: {df.columns.tolist()}")

    # Ensure we are working with a copy to avoid SettingWithCopy warnings
    temp_df = df.copy()

    # Convert WKT strings to Shapely objects
    # We use errors='coerce' logic implicitly by catching failures
    try:
        temp_df['geometry'] = temp_df[wkt_col].apply(wkt.loads)
    except Exception as e:
        # If it fails, try cleaning common WKT syntax errors
        print(f"DEBUG: WKT parsing failed, attempting cleanup. Error: {e}")
        temp_df['geometry'] = temp_df[wkt_col].str.strip().apply(wkt.loads)

    gdf = gpd.GeoDataFrame(temp_df, geometry='geometry', crs=crs)
    return gdf


def calculate_spatial_autocorrelation(df, gdf):
    """
    Runs Global Moran's I on model residuals.
    Strictly aligns the weights matrix with the observation index to prevent silent errors.
    """
    # 1. Align and project
    merged = gdf.merge(df[['zip_code', 'residuals']], on='zip_code').dropna(subset=['residuals'])
    merged = merged.to_crs(SEATTLE_CRS)  # Moran's I is more robust on projected coordinates

    # 2. Weights Matrix Construction
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Use Queen contiguity for neighborhood-based urban studies
        w = libpysal.weights.Queen.from_dataframe(merged)

    # 3. Handling Islands (The 'Shablona' Way)
    if w.islands:
        island_zips = merged.iloc[w.islands]['zip_code'].tolist()
        logger.warning(f"Spatial islands detected and removed from Moran's I: {island_zips}")

        # Filter out islands and re-build weights
        merged = merged.drop(merged.index[w.islands])
        w = libpysal.weights.Queen.from_dataframe(merged)

    w.transform = 'r'  # Row-standardize weights

    # 4. Statistical Test
    mi = Moran(merged['residuals'].values, w)

    logger.info(f"Global Moran's I calculated: {mi.I:.4f} (p-value: {mi.p_sim:.4f})")
    return mi

def check_spatial_bridge(locations_df, geography_df, join_col='location_id'):
    """
    Validates the connection between site locations and geographic polygons.
    Returns the set of common IDs and IDs present in locations but missing in geography.
    """
    if join_col not in locations_df.columns or join_col not in geography_df.columns:
        raise KeyError(f"Join column '{join_col}' must exist in both dataframes.")

    loc_ids = set(locations_df[join_col].unique())
    geo_ids = set(geography_df[join_col].unique())

    common_ids = loc_ids.intersection(geo_ids)
    missing_ids = loc_ids - geo_ids

    return common_ids, missing_ids

def plot_residuals(df, gdf, output_path=None):
    """
    Generates a high-contrast choropleth of model residuals.
    Red = Model under-predicted DSR (High digital activity)
    Blue = Model over-predicted DSR (High social activity)
    """
    merged = gdf.merge(df, on='zip_code', how='left')

    fig, ax = plt.subplots(1, 1, figsize=(12, 10))

    # Center the colorbar at 0 (White)
    limit = max(abs(merged['residuals'].min()), abs(merged['residuals'].max()))
    norm = TwoSlopeNorm(vcenter=0, vmin=-limit, vmax=limit)

    plot = merged.plot(
        column='residuals',
        cmap='RdBu_r',  # Red-Blue diverging
        norm=norm,
        legend=True,
        ax=ax,
        edgecolor='black',
        linewidth=0.3,
        missing_kwds={'color': '#e0e0e0', 'label': 'No Data'}
    )

    # Add high-contrast labels using the existing label utility
    add_district_labels(ax, merged.dropna(subset=['residuals']), 'zip_code')

    ax.set_axis_off()
    ax.set_title("DSR Model Residuals: Geographic Prediction Error", fontsize=15, pad=20)

    # Contextual annotation for recruiters
    ax.annotate("Blue: Over-predicted DSR\nRed: Under-predicted DSR",
                xy=(0.05, 0.05), xycoords='axes fraction', fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

    if output_path:
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
    return fig


def add_district_labels(ax, gdf, label_col):
    """Places high-contrast labels on the representative point of each polygon."""
    for _, row in gdf.iterrows():
        point = row['geometry'].representative_point().coords[0]
        txt = ax.text(point[0], point[1], s=row[label_col],
                      fontsize=7, color='white', ha='center', fontweight='bold')
        txt.set_path_effects([patheffects.withStroke(linewidth=1.5, foreground='black')])