#!/usr/bin/env python3
"""
Generate high-quality PNGs of world population potential.
Uses the same technique as the sharp USA renders.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.spatial import Delaunay
from pathlib import Path

def load_potential_data(csv_path):
    """Load lon/lat/potential from CSV."""
    df = pd.read_csv(csv_path)
    lons = df['LONGITUDE'].values
    lats = df['LATITUDE'].values
    potentials = df['POTENTIAL'].values
    return lons, lats, potentials

def create_figure(lons, lats, potentials, tri, z_scaled, color_normalized,
                  colorscale, title, camera, lighting):
    """Create a Mesh3d figure with given parameters."""
    fig = go.Figure(data=[go.Mesh3d(
        x=lons,
        y=lats,
        z=z_scaled,
        i=tri.simplices[:, 0],
        j=tri.simplices[:, 1],
        k=tri.simplices[:, 2],
        intensity=color_normalized,
        colorscale=colorscale,
        showscale=False,
        lighting=lighting,
        flatshading=False,
        hoverinfo='skip'
    )])

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis=dict(title='Longitude (°)', showgrid=True, visible=True),
            yaxis=dict(title='Latitude (°)', showgrid=True, visible=True),
            zaxis=dict(title='', showgrid=False, visible=False),
            aspectmode='data',
            camera=camera,
            bgcolor='white'
        ),
        width=1920,
        height=1080,
        showlegend=False,
        paper_bgcolor='white',
        margin=dict(l=0, r=0, t=40, b=0)
    )

    return fig

def create_discrete_4color():
    """Create discrete 4-color scale for AMS printing."""
    return [
        [0.00, 'rgb(0, 0, 139)'],      # dark blue
        [0.25, 'rgb(0, 0, 139)'],      # dark blue (hard edge)
        [0.25, 'rgb(0, 191, 255)'],    # cyan/deep sky blue
        [0.50, 'rgb(0, 191, 255)'],    # cyan (hard edge)
        [0.50, 'rgb(255, 255, 0)'],    # yellow
        [0.75, 'rgb(255, 255, 0)'],    # yellow (hard edge)
        [0.75, 'rgb(220, 20, 60)'],    # red/crimson
        [1.00, 'rgb(220, 20, 60)']     # red
    ]

def main():
    # Load data
    csv_path = 'output/world_gpw_hex30mi_30mile_potentials.csv'
    print(f"Loading {csv_path}...")
    lons, lats, potentials = load_potential_data(csv_path)
    print(f"Loaded {len(lons):,} points")

    # Build triangulation
    print("Building Delaunay triangulation...")
    tri = Delaunay(np.column_stack((lons, lats)))
    print(f"  {len(tri.simplices):,} triangles")

    # Z scaling: use 0.05 for printable version
    print("Applying Z scaling (0.05 for printing)...")
    p_shifted = potentials - potentials.min()
    lon_range = lons.max() - lons.min()
    z_normalized = p_shifted / p_shifted.max()
    z_scaled = z_normalized * (lon_range * 0.05)

    # Color scaling: LOG for detail
    print("Applying log color scaling...")
    color_values = np.log10(p_shifted + 1)
    color_normalized = color_values / color_values.max()

    # Colorscales
    colorscales = {
        'Cividis': 'Cividis',
        'Discrete4': create_discrete_4color(),
        'Greys': 'Greys',
    }

    # Camera angle (north-facing)
    camera = dict(eye=dict(x=0, y=-2.0, z=0.8))

    # Lighting
    lighting = dict(ambient=0.3, diffuse=0.9, specular=0.5)

    # Output directory
    output_dir = Path('output/world_hex30mi_30mile_hq')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate images
    for cs_name, cs_value in colorscales.items():
        filename = f"world_30mile_print_{cs_name.lower()}.png"
        output_path = output_dir / filename

        print(f"Generating {filename}...")
        title = f"World Population Potential - 30mi Print ({cs_name})"

        fig = create_figure(lons, lats, potentials, tri, z_scaled, color_normalized,
                          cs_value, title, camera, lighting)
        fig.write_image(str(output_path))
        print(f"  Saved to {output_path}")

    print(f"\nDone! Generated {len(colorscales)} images")
    print(f"Open with: open {output_dir}")

if __name__ == '__main__':
    main()
