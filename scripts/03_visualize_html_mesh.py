#!/usr/bin/env python3
"""
Visualize USA 1/d³ potential using go.Mesh3d (triangle mesh).

Input:  output/usa/triangle_centers_d3_potential.csv
Output: output/usa/preview_mesh_8pct_z.html

Visualization:
- Triangle mesh (preserves actual data structure)
- 8% Z aspect ratio (2cm height / 25cm width equivalent)
- Linear Z scale
- Monochrome grayscale
- Lat/long axis labels
- Interactive drag/rotate/zoom
"""

import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Delaunay
from pathlib import Path

print("Loading USA triangle center data...")
data = np.loadtxt('output/usa/triangle_centers_d3_potential.csv', delimiter=',')

lons = data[:, 0]
lats = data[:, 1]
potentials = data[:, 2]

print(f"Loaded {len(data):,} triangle centers")
print(f"Lon range: {lons.min():.2f} to {lons.max():.2f}")
print(f"Lat range: {lats.min():.2f} to {lats.max():.2f}")
print(f"Potential range: {potentials.min():.2e} to {potentials.max():.2e}")

# Create triangulation for mesh
print("Creating Delaunay triangulation...")
points = np.column_stack((lons, lats))
tri = Delaunay(points)
print(f"Created {len(tri.simplices):,} triangles")

# Calculate Z aspect ratio: 8% (2cm / 25cm)
z_aspect = 0.08

# Geographic bounds
lon_range = lons.max() - lons.min()
lat_range = lats.max() - lats.min()

# Scale Z to 8% of width
# Normalize potential to 0-1, then scale to 8% of lon_range
pot_min, pot_max = potentials.min(), potentials.max()
z_normalized = (potentials - pot_min) / (pot_max - pot_min)
z_scaled = z_normalized * (lon_range * z_aspect)

print(f"\nScaling:")
print(f"  Geographic: {lon_range:.1f}° × {lat_range:.1f}°")
print(f"  Z range: 0 to {z_scaled.max():.2f}° ({z_aspect*100:.1f}% of width)")
print(f"  Z aspect ratio: {z_aspect*100:.1f}%")

# Create mesh
fig = go.Figure(data=[
    go.Mesh3d(
        x=lons,
        y=lats,
        z=z_scaled,
        i=tri.simplices[:, 0],
        j=tri.simplices[:, 1],
        k=tri.simplices[:, 2],
        intensity=z_scaled,
        colorscale='Greys',
        showscale=True,
        colorbar=dict(
            title="Height<br>(scaled)"
        ),
        hovertemplate=(
            'Lon: %{x:.2f}°<br>' +
            'Lat: %{y:.2f}°<br>' +
            'Height: %{z:.3f}°<br>' +
            '<extra></extra>'
        ),
        lighting=dict(
            ambient=0.5,
            diffuse=0.8,
            specular=0.2,
            roughness=0.5
        ),
        flatshading=False
    )
])

fig.update_layout(
    title=dict(
        text="USA Population Potential - Triangle Mesh<br>" +
             f"<sub>1/d³ potential | {z_aspect*100:.1f}% Z aspect | Linear scale | {len(tri.simplices):,} triangles</sub>",
        font=dict(size=16)
    ),
    scene=dict(
        xaxis=dict(
            title='Longitude (°)',
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            showticklabels=True,
            dtick=10  # Tick every 10 degrees
        ),
        yaxis=dict(
            title='Latitude (°)',
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            showticklabels=True,
            dtick=5  # Tick every 5 degrees
        ),
        zaxis=dict(
            title='Potential (scaled)',
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            showticklabels=True
        ),
        aspectmode='data',
        camera=dict(
            eye=dict(x=1.5, y=1.5, z=1.2),
            center=dict(x=0, y=0, z=0)
        ),
        bgcolor='white'
    ),
    width=1600,
    height=1000,
    paper_bgcolor='white'
)

output_path = Path('output/usa/preview_mesh_8pct_z.html')
print(f"\nSaving to {output_path}...")
fig.write_html(str(output_path))
print(f"✓ Done! Open {output_path}")
