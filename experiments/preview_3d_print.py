#!/usr/bin/env python3
"""
Preview 1/d³ potential surfaces scaled for 3D printing.
Shows what USA and world visualizations will look like with print constraints.

Print specs:
- Base: 25cm × 15cm
- Max height: 2cm (peaks)
- Monochrome (grayscale height map)

Usage: python3 preview_3d_print.py [usa|world]
"""

import sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


def load_usa_data():
    """Load USA census tract data from existing computation."""
    # Check for existing USA potential data
    csv_path = Path("output/census_potential_d3.csv")

    if not csv_path.exists():
        print(f"USA data not found at {csv_path}")
        print("Checking for pre-computed data in gridded repo...")
        alt_path = Path.home() / "git" / "gridded" / "res" / "potential_1_over_d3_selfexclude" / "usa_census_tracts.csv"
        if alt_path.exists():
            csv_path = alt_path
        else:
            print("ERROR: No USA census tract potential data found.")
            print("Please run a USA potential calculation first.")
            return None

    print(f"Loading USA data from {csv_path}...")
    df = pd.read_csv(csv_path, names=['type', 'pop', 'lat', 'lon', 'potential'])

    return df


def load_world_data():
    """Load world 15-minute grid data."""
    csv_path = Path.home() / "git" / "gridded" / "res" / "potential_1_over_d3_selfexclude" / "raw_potential.csv"

    if not csv_path.exists():
        print(f"ERROR: World data not found at {csv_path}")
        return None

    print(f"Loading world data from {csv_path}...")
    df = pd.read_csv(csv_path, names=['type', 'pop', 'lat', 'lon', 'potential'])

    return df


def create_print_preview(df, region_name, base_width_cm=25, base_height_cm=15, max_z_cm=2):
    """
    Create HTML preview scaled for 3D printing.

    Args:
        df: DataFrame with lat, lon, potential columns
        region_name: 'USA' or 'World'
        base_width_cm: Print base width in cm (longitude direction)
        base_height_cm: Print base height in cm (latitude direction)
        max_z_cm: Maximum peak height in cm
    """

    # Get unique coordinates and create grid
    unique_lats = sorted(df['lat'].unique(), reverse=True)
    unique_lons = sorted(df['lon'].unique())

    nrows, ncols = len(unique_lats), len(unique_lons)
    print(f"Grid size: {nrows} × {ncols}")

    # Create meshgrid
    lon_grid, lat_grid = np.meshgrid(unique_lons, unique_lats)

    # Reshape potential values
    df_sorted = df.sort_values(['lat', 'lon'], ascending=[False, True])
    potential_grid = df_sorted['potential'].values.reshape(nrows, ncols)

    # Get geographic bounds
    lon_min, lon_max = unique_lons[0], unique_lons[-1]
    lat_min, lat_max = unique_lats[-1], unique_lats[0]
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min

    print(f"Geographic bounds: Lon [{lon_min:.1f}, {lon_max:.1f}], Lat [{lat_min:.1f}, {lat_max:.1f}]")
    print(f"Potential range: {potential_grid.min():.2e} to {potential_grid.max():.2e}")

    # Scale coordinates to print dimensions (in cm)
    # We want to preserve aspect ratio
    if lon_range > lat_range:
        # Width-constrained
        x_scale = base_width_cm / lon_range
        y_scale = x_scale  # Keep aspect ratio
        actual_height = lat_range * y_scale
        actual_width = base_width_cm
    else:
        # Height-constrained
        y_scale = base_height_cm / lat_range
        x_scale = y_scale
        actual_width = lon_range * x_scale
        actual_height = base_height_cm

    x_print = (lon_grid - lon_min) * x_scale
    y_print = (lat_grid - lat_min) * y_scale

    # Scale Z to max_z_cm
    # Use the potential directly, normalized to max height
    z_raw = potential_grid
    z_min, z_max = z_raw.min(), z_raw.max()

    # Normalize to 0-max_z_cm range
    z_print = (z_raw - z_min) / (z_max - z_min) * max_z_cm

    print(f"\nPrint dimensions:")
    print(f"  Base: {actual_width:.1f}cm × {actual_height:.1f}cm")
    print(f"  Height: 0 to {max_z_cm}cm")
    print(f"  Z aspect ratio: {max_z_cm / actual_width * 100:.1f}% (height/width)")

    # Create monochrome surface
    fig = go.Figure(data=[
        go.Surface(
            x=x_print,
            y=y_print,
            z=z_print,
            colorscale='Greys',  # Monochrome for 3D printing
            showscale=True,
            colorbar=dict(
                title="Height (cm)",
                titleside="right",
                tickmode="linear",
                tick0=0,
                dtick=0.5
            ),
            lighting=dict(
                ambient=0.4,
                diffuse=0.8,
                specular=0.3,
                roughness=0.5
            ),
            hovertemplate='X: %{x:.1f}cm<br>Y: %{y:.1f}cm<br>Z: %{z:.2f}cm<extra></extra>'
        )
    ])

    # Update layout
    fig.update_layout(
        title=dict(
            text=f"{region_name} Population Potential - 3D Print Preview<br>" +
                 f"<sub>1/d⁴ force law (1/d³ potential) | Base: {actual_width:.1f}×{actual_height:.1f}cm | Max height: {max_z_cm}cm</sub>",
            font=dict(size=16)
        ),
        scene=dict(
            xaxis=dict(title='Width (cm)', range=[0, actual_width]),
            yaxis=dict(title='Depth (cm)', range=[0, actual_height]),
            zaxis=dict(title='Height (cm)', range=[0, max_z_cm]),
            aspectmode='data',  # True to scale
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2),
                center=dict(x=0, y=0, z=0)
            ),
            bgcolor='white'
        ),
        width=1200,
        height=800,
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    # Save HTML
    output_path = Path(f"output/{region_name.lower()}_3d_print_preview.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving to {output_path}...")
    fig.write_html(str(output_path))
    print(f"✓ Saved: {output_path}")

    return output_path


def main():
    region = sys.argv[1].lower() if len(sys.argv) > 1 else 'usa'

    if region not in ['usa', 'world']:
        print("Usage: python3 preview_3d_print.py [usa|world]")
        sys.exit(1)

    print("="*70)
    print(f"3D PRINT PREVIEW: {region.upper()}")
    print("="*70)
    print()

    # Load data
    if region == 'usa':
        df = load_usa_data()
    else:
        df = load_world_data()

    if df is None:
        sys.exit(1)

    # Create preview
    output_path = create_print_preview(df, region.upper())

    print()
    print("="*70)
    print("✓ Preview complete!")
    print("="*70)
    print()
    print(f"Open {output_path} in your browser to view the 3D print preview.")
    print()
    print("The visualization shows:")
    print("  - Actual print dimensions (25×15cm base, 2cm max height)")
    print("  - Monochrome grayscale (suitable for single-material printing)")
    print("  - True-to-scale aspect ratio")
    print()
    print("Next steps:")
    print("  1. Review the preview and check if details are visible")
    print("  2. Decide if height needs adjustment for printability")
    print("  3. Generate OBJ file for actual 3D printing")


if __name__ == "__main__":
    main()
