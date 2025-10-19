#!/usr/bin/env python3
"""
Generate interactive 3D scatter visualization from potential data at irregular points.

For use with census tracts or other non-gridded data.

Usage: python3 visualize_potential_scatter.py <input_csv> [output_html]
"""

import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

try:
    from scipy.interpolate import griddata
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("Note: scipy not available, will use scatter plots only (no interpolation)")


def load_potential_data(csv_path):
    """Load potential field data from CSV."""
    print(f"Loading data from {csv_path}...")

    # Format: A,population,lat,lon,potential
    df = pd.read_csv(csv_path,
                     names=['type', 'pop', 'lat', 'lon', 'potential'],
                     dtype={'type': str, 'pop': float, 'lat': float, 'lon': float, 'potential': float})

    print(f"Loaded {len(df)} data points")
    print(f"Lat range: {df['lat'].min():.2f} to {df['lat'].max():.2f}")
    print(f"Lon range: {df['lon'].min():.2f} to {df['lon'].max():.2f}")
    print(f"Potential range: {df['potential'].min():.0f} to {df['potential'].max():.0f}")

    return df


def create_interpolated_surface(df, grid_resolution=100):
    """Interpolate scattered points onto a regular grid for surface plotting."""
    print(f"Interpolating to {grid_resolution}x{grid_resolution} grid...")

    # Extract data
    lons = df['lon'].values
    lats = df['lat'].values
    potentials = df['potential'].values

    # Create regular grid
    lon_min, lon_max = lons.min(), lons.max()
    lat_min, lat_max = lats.min(), lats.max()

    lon_grid_1d = np.linspace(lon_min, lon_max, grid_resolution)
    lat_grid_1d = np.linspace(lat_min, lat_max, grid_resolution)
    lon_grid, lat_grid = np.meshgrid(lon_grid_1d, lat_grid_1d)

    # Interpolate using cubic interpolation
    points = np.column_stack((lons, lats))
    potential_grid = griddata(points, potentials, (lon_grid, lat_grid), method='cubic')

    # Fill any NaN values with nearest neighbor
    nan_mask = np.isnan(potential_grid)
    if nan_mask.any():
        print(f"  Filling {nan_mask.sum()} NaN values with nearest neighbor...")
        potential_grid_nn = griddata(points, potentials, (lon_grid, lat_grid), method='nearest')
        potential_grid[nan_mask] = potential_grid_nn[nan_mask]

    return lon_grid, lat_grid, potential_grid


def create_scatter_plot(df, title="Population Gravitational Potential", transform="log", z_scale=1.0):
    """Create 3D scatter plot of irregular points."""
    print("Creating 3D scatter plot...")

    # Transform potential for better visualization
    potentials = df['potential'].values

    if transform == "log":
        z_normalized = np.log10(potentials + 1)
        z_label = "log₁₀(Potential)"
    elif transform == "log2":
        z_normalized = np.log10(np.log10(potentials + 1) + 1)
        z_label = "log₁₀(log₁₀(Potential))"
    elif transform == "sqrt":
        z_normalized = np.sqrt(potentials)
        z_label = "√(Potential)"
    elif transform == "cbrt":
        z_normalized = np.cbrt(potentials)
        z_label = "∛(Potential)"
    elif transform == "raw":
        z_normalized = potentials * z_scale
        z_label = f"Potential × {z_scale}"
    else:
        z_normalized = potentials
        z_label = "Potential"

    print(f"  Transform: {transform}, z-scale: {z_scale}")
    print(f"  Z range: {z_normalized.min():.2f} to {z_normalized.max():.2f}")

    # Calculate aspect ratio
    avg_lat = df['lat'].mean()
    cos_avg_lat = np.cos(np.radians(avg_lat))

    lon_range = df['lon'].max() - df['lon'].min()
    lat_range = df['lat'].max() - df['lat'].min()

    aspect_x = lon_range * cos_avg_lat / lat_range
    aspect_y = 1.0
    aspect_z = 0.3

    fig = go.Figure(data=[go.Scatter3d(
        x=df['lon'],
        y=df['lat'],
        z=z_normalized,
        mode='markers',
        marker=dict(
            size=3,
            color=z_normalized,
            colorscale='Viridis',
            colorbar=dict(
                title=dict(text=z_label, side="right")
            ),
            opacity=0.8
        ),
        hovertemplate='<b>Tract</b><br>' +
                      'Lon: %{x:.3f}<br>' +
                      'Lat: %{y:.3f}<br>' +
                      f'{z_label}: ' + '%{z:.2f}<br>' +
                      '<extra></extra>'
    )])

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        scene=dict(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            zaxis_title=z_label,
            camera=dict(
                eye=dict(x=1.5, y=-1.0, z=1.2),
                up=dict(x=0, y=1, z=0)
            ),
            aspectmode='manual',
            aspectratio=dict(x=aspect_x, y=aspect_y, z=aspect_z)
        ),
        width=1400,
        height=900,
        hovermode='closest'
    )

    return fig


def create_surface_plot(lon_grid, lat_grid, potential_grid, title="Population Gravitational Potential"):
    """Create interpolated surface plot."""
    print("Creating 3D surface plot...")

    # Normalize potential for better visualization
    z_normalized = np.log10(potential_grid + 1)
    z_label = "log₁₀(Potential)"

    # Calculate aspect ratio
    avg_lat = np.nanmean(lat_grid)
    cos_avg_lat = np.cos(np.radians(avg_lat))

    lon_range = np.nanmax(lon_grid) - np.nanmin(lon_grid)
    lat_range = np.nanmax(lat_grid) - np.nanmin(lat_grid)

    aspect_x = lon_range * cos_avg_lat / lat_range
    aspect_y = 1.0
    aspect_z = 0.3

    fig = go.Figure(data=[go.Surface(
        x=lon_grid,
        y=lat_grid,
        z=z_normalized,
        colorscale='Viridis',
        colorbar=dict(
            title=dict(text=z_label, side="right")
        ),
        lighting=dict(
            ambient=0.5,
            diffuse=0.8,
            specular=0.3,
            roughness=0.5,
            fresnel=0.2
        ),
        hovertemplate='<b>Location</b><br>' +
                      'Lon: %{x:.3f}<br>' +
                      'Lat: %{y:.3f}<br>' +
                      f'{z_label}: ' + '%{z:.2f}<br>' +
                      '<extra></extra>'
    )])

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        scene=dict(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            zaxis_title=z_label,
            camera=dict(
                eye=dict(x=1.5, y=-1.0, z=1.2),
                up=dict(x=0, y=1, z=0)
            ),
            aspectmode='manual',
            aspectratio=dict(x=aspect_x, y=aspect_y, z=aspect_z)
        ),
        width=1400,
        height=900,
        hovermode='closest'
    )

    return fig


def main():
    if len(sys.argv) < 2:
        print("ERROR: Missing input file", file=sys.stderr)
        print(file=sys.stderr)
        print("Usage: python3 visualize_potential_scatter.py <input_csv> [output_html] [--transform TYPE] [--z-scale SCALE]", file=sys.stderr)
        print(file=sys.stderr)
        print("Transform types: log (default), log2 (double-log), sqrt, cbrt, raw", file=sys.stderr)
        print(file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  python3 visualize_potential_scatter.py output/sf_bay_potential_d3.csv", file=sys.stderr)
        print("  python3 visualize_potential_scatter.py output/usa.csv output/usa.html --transform raw --z-scale 0.00001", file=sys.stderr)
        print("  python3 visualize_potential_scatter.py output/usa.csv output/usa.html --transform sqrt", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]

    # Parse output path
    if len(sys.argv) >= 3 and not sys.argv[2].startswith('--'):
        output_path = sys.argv[2]
        arg_start = 3
    else:
        # Auto-generate output name
        input_stem = Path(input_path).stem
        output_path = f"output/{input_stem}_viz.html"
        arg_start = 2

    # Parse optional arguments
    transform = "log"
    z_scale = 1.0

    i = arg_start
    while i < len(sys.argv):
        if sys.argv[i] == '--transform' and i + 1 < len(sys.argv):
            transform = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--z-scale' and i + 1 < len(sys.argv):
            z_scale = float(sys.argv[i + 1])
            i += 2
        else:
            print(f"WARNING: Unknown argument: {sys.argv[i]}", file=sys.stderr)
            i += 1

    if not Path(input_path).exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    Path("output").mkdir(exist_ok=True)

    # Load data
    df = load_potential_data(input_path)

    # Determine visualization type based on data size
    n_points = len(df)

    if HAS_SCIPY and n_points > 5000:
        print(f"\nLarge dataset ({n_points} points) - creating interpolated surface...")
        lon_grid, lat_grid, potential_grid = create_interpolated_surface(df, grid_resolution=150)
        fig = create_surface_plot(lon_grid, lat_grid, potential_grid)
    elif HAS_SCIPY and n_points > 2000:
        print(f"\nMedium dataset ({n_points} points) - creating interpolated surface...")
        lon_grid, lat_grid, potential_grid = create_interpolated_surface(df, grid_resolution=100)
        fig = create_surface_plot(lon_grid, lat_grid, potential_grid)
    else:
        if not HAS_SCIPY:
            print(f"\nCreating scatter plot ({n_points} points)...")
        else:
            print(f"\nSmall dataset ({n_points} points) - creating scatter plot...")
        fig = create_scatter_plot(df, transform=transform, z_scale=z_scale)

    # Save
    print(f"\nSaving to {output_path}...")
    fig.write_html(output_path)

    print()
    print("="*60)
    print(f"✓ Visualization saved to: {output_path}")
    print("="*60)
    print("\nOpen in browser to view interactive 3D visualization.")
    print("You can rotate, zoom, and hover over points to explore.")


if __name__ == "__main__":
    main()
