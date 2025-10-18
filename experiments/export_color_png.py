#!/usr/bin/env python3
"""
Generate PNGs with independent Z scaling and color scaling.
Test different colorscales with linear Z + log color.
"""

import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Delaunay
from pathlib import Path
import sys

def load_potential_data(csv_path):
    """Load triangle centers + potential from CSV."""
    data = np.loadtxt(csv_path, delimiter=',')
    lons = data[:, 0]
    lats = data[:, 1]
    potentials = data[:, 2]
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

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 export_color_png.py <region>")
        print("Example: python3 export_color_png.py usa_grid_5mi")
        sys.exit(1)

    region = sys.argv[1]

    # Load data
    csv_path = f'output/{region}/triangle_centers_d3_potential_2mile.csv'
    print(f"Loading {csv_path}...")
    lons, lats, potentials = load_potential_data(csv_path)
    print(f"Loaded {len(lons):,} sample points")

    # Build triangulation (once)
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

    # Colorscales to test
    colorscales = {
        'Greys': 'Greys',
        'Viridis': 'Viridis',
        'Plasma': 'Plasma',
        'Inferno': 'Inferno',
        'Cividis': 'Cividis',
        'Blues': 'Blues',
        'YlOrRd': 'YlOrRd',
        'Hot': 'Hot',
    }

    # Camera angles (quick mode)
    cameras = {
        'north': dict(eye=dict(x=0, y=-2.0, z=0.8)),
        'northeast': dict(eye=dict(x=1.4, y=-1.4, z=0.8)),
    }

    # Lighting
    lighting = dict(ambient=0.3, diffuse=0.9, specular=0.5)

    # Output directory
    output_dir = Path(f'output/{region}/renders_color')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate images
    total = len(colorscales) * len(cameras)
    count = 0

    for cs_name, cs_value in colorscales.items():
        for cam_name, camera in cameras.items():
            count += 1
            title = f"{region.replace('_', ' ').title()} - Linear Z + Log {cs_name} - {cam_name}"
            filename = f"{region}_linear_z_log_{cs_name.lower()}_{cam_name}.png"
            output_path = output_dir / filename

            print(f"[{count}/{total}] Generating {filename}...")

            fig = create_figure(lons, lats, potentials, tri, z_scaled, color_normalized,
                              cs_value, title, camera, lighting)
            fig.write_image(str(output_path))
            print(f"  Saved to {output_path}")

    print(f"\nDone! Generated {total} images")
    print(f"Open with: open {output_dir}")

if __name__ == '__main__':
    main()
