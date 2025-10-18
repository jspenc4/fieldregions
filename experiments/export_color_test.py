#!/usr/bin/env python3
"""
Generate interactive HTML with independent Z scaling and color scaling.
Test case: linear Z height + log color intensity
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
        print("Usage: python3 export_color_test.py <region>")
        print("Example: python3 export_color_test.py usa_grid_5mi")
        sys.exit(1)

    region = sys.argv[1]

    # Load data
    csv_path = f'output/{region}/triangle_centers_d3_potential_2mile.csv'
    print(f"Loading {csv_path}...")
    lons, lats, potentials = load_potential_data(csv_path)
    print(f"Loaded {len(lons):,} sample points")

    # Build triangulation
    print("Building Delaunay triangulation...")
    tri = Delaunay(np.column_stack((lons, lats)))

    # Z scaling: LINEAR (dramatic peaks)
    print("Applying linear Z scaling...")
    p_shifted = potentials - potentials.min()
    lon_range = lons.max() - lons.min()
    z_normalized = p_shifted / p_shifted.max()
    z_scaled = z_normalized * (lon_range * 0.08)

    # Color scaling: LOG (reveal detail)
    print("Applying log color scaling...")
    color_values = np.log10(p_shifted + 1)
    color_normalized = color_values / color_values.max()

    print(f"Z range: {z_scaled.min():.4f} to {z_scaled.max():.4f}")
    print(f"Color range: {color_normalized.min():.4f} to {color_normalized.max():.4f}")

    # Create figure with Viridis colorscale for better visibility
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
        colorbar=dict(title='Log(Potential)'),
        lighting=dict(ambient=0.4, diffuse=0.8, specular=0.3),
        flatshading=False,
        hoverinfo='skip'
    )])

    # Camera: north view (looking from south)
    camera = dict(eye=dict(x=0, y=-2.0, z=0.8))

    fig.update_layout(
        title=f"{region.replace('_', ' ').title()} - Linear Z + Log Color",
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
    output_path = f'output/{region}/{region}_linear_z_log_color.html'
    print(f"Saving to {output_path}...")
    fig.write_html(output_path)
    print(f"Done! Open with: open {output_path}")

if __name__ == '__main__':
    main()
