#!/usr/bin/env python3
"""
Generate HTML with independent Z scaling and color scaling, with threshold cutoff.
Test: linear Z + log color with threshold to hide sparse grid artifacts
"""

import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Delaunay
import sys

def load_potential_data(csv_path):
    """Load triangle centers + potential from CSV."""
    data = np.loadtxt(csv_path, delimiter=',')
    lons = data[:, 0]
    lats = data[:, 1]
    potentials = data[:, 2]
    return lons, lats, potentials

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 export_color_threshold.py <region> [threshold_percentile]")
        print("Example: python3 export_color_threshold.py usa_grid_5mi 10")
        sys.exit(1)

    region = sys.argv[1]
    threshold_pct = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0

    # Load data
    csv_path = f'output/{region}/triangle_centers_d3_potential_2mile.csv'
    print(f"Loading {csv_path}...")
    lons, lats, potentials = load_potential_data(csv_path)
    print(f"Loaded {len(lons):,} sample points")

    # Calculate threshold
    threshold_value = np.percentile(potentials, threshold_pct)
    print(f"Threshold ({threshold_pct}th percentile): {threshold_value:.2e}")
    print(f"Points below threshold: {np.sum(potentials < threshold_value):,} ({100*np.sum(potentials < threshold_value)/len(potentials):.1f}%)")

    # Build triangulation
    print("Building Delaunay triangulation...")
    tri = Delaunay(np.column_stack((lons, lats)))

    # Z scaling: LINEAR (dramatic peaks)
    print("Applying linear Z scaling...")
    p_shifted = potentials - potentials.min()
    lon_range = lons.max() - lons.min()
    z_normalized = p_shifted / p_shifted.max()
    z_scaled = z_normalized * (lon_range * 0.08)

    # Color scaling: LOG with threshold cutoff
    print("Applying log color scaling with threshold...")
    color_values = np.log10(p_shifted + 1)

    # Apply threshold - set values below threshold to minimum
    color_values_thresholded = color_values.copy()
    below_threshold = potentials < threshold_value
    color_values_thresholded[below_threshold] = 0  # Set to minimum

    # Normalize only the above-threshold values
    if color_values_thresholded.max() > 0:
        color_normalized = color_values_thresholded / color_values_thresholded.max()
    else:
        color_normalized = color_values_thresholded

    print(f"Z range: {z_scaled.min():.4f} to {z_scaled.max():.4f}")
    print(f"Color range: {color_normalized.min():.4f} to {color_normalized.max():.4f}")
    print(f"Points at color minimum: {np.sum(color_normalized == 0):,}")

    # Create figure with Viridis colorscale
    print("Creating figure...")
    fig = go.Figure(data=[go.Mesh3d(
        x=lons,
        y=lats,
        z=z_scaled,
        i=tri.simplices[:, 0],
        j=tri.simplices[:, 1],
        k=tri.simplices[:, 2],
        intensity=color_normalized,
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title=f'Log(Potential)<br>{threshold_pct}% threshold'),
        lighting=dict(ambient=0.4, diffuse=0.8, specular=0.3),
        flatshading=False,
        hoverinfo='skip'
    )])

    # Camera: north view (looking from south)
    camera = dict(eye=dict(x=0, y=-2.0, z=0.8))

    fig.update_layout(
        title=f"{region.replace('_', ' ').title()} - Linear Z + Log Color (Threshold {threshold_pct}%)",
        scene=dict(
            xaxis=dict(title='Longitude (°)', showgrid=True, visible=True),
            yaxis=dict(title='Latitude (°)', showgrid=True, visible=True),
            zaxis=dict(title='Population Potential', showgrid=False, visible=True),
            aspectmode='data',
            camera=camera,
            bgcolor='white'
        ),
        width=1400,
        height=900,
        paper_bgcolor='white',
        margin=dict(l=0, r=0, t=40, b=0)
    )

    # Save HTML
    output_path = f'output/{region}/{region}_linear_z_log_color_threshold_{int(threshold_pct)}pct.html'
    print(f"Saving to {output_path}...")
    fig.write_html(output_path)
    print(f"Done! Open with: open {output_path}")

if __name__ == '__main__':
    main()
