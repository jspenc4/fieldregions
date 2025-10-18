#!/usr/bin/env python3
"""
Generate HTML visualization for NYC area with custom Z scaling.
"""

import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Delaunay

# Load NYC subset data
print("Loading NYC subset...")
data = np.loadtxt('/tmp/nyc_subset.csv', delimiter=',')
lons = data[:, 0]
lats = data[:, 1]
potentials = data[:, 2]

print(f"Points: {len(lons):,}")
print(f"Potential range: {potentials.min():.2e} to {potentials.max():.2e}")

# Build triangulation
print("Building Delaunay triangulation...")
tri = Delaunay(np.column_stack((lons, lats)))
print(f"Triangles: {len(tri.simplices):,}")

# Z scaling: LINEAR with 4% aspect ratio
p_shifted = potentials - potentials.min()
lon_range = lons.max() - lons.min()
z_normalized = p_shifted / p_shifted.max()
z_scaled = z_normalized * (lon_range * 0.04)

# Color scaling: LOG (reveal detail)
color_values = np.log10(p_shifted + 1)
color_normalized = color_values / color_values.max()

print(f"Lon range: {lon_range:.3f}°")
print(f"Z range: {z_scaled.min():.4f} to {z_scaled.max():.4f}")
print(f"Color range: {color_normalized.min():.4f} to {color_normalized.max():.4f}")

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
    colorbar=dict(title='Log(Potential)'),
    lighting=dict(ambient=0.4, diffuse=0.8, specular=0.3),
    flatshading=False,
    hoverinfo='skip'
)])

# Camera: north view (looking from south)
camera = dict(eye=dict(x=0, y=-2.0, z=0.8))

fig.update_layout(
    title=f"NYC Metro - Natural Topological Sampling (Linear Z @ 4% + Log Color)",
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
output_path = 'output/usa_natural/nyc_area_4pct.html'
print(f"Saving to {output_path}...")
fig.write_html(output_path)
print(f"Done! Open with: open {output_path}")
