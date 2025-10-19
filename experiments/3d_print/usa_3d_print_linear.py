#!/usr/bin/env python3
"""
Generate USA 1/d³ potential preview for 3D printing using pre-calculated data.
Linear Z scale: 0-2cm, monochrome, 25×15cm base, triangle mesh.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Delaunay

print("Loading USA census tract 1/d³ potential data...")
df = pd.read_csv('output/census_potential_d3.csv',
                 names=['type', 'pop', 'lat', 'lon', 'potential'])
print(f"Loaded {len(df)} census tracts")

# Create Delaunay triangulation
print("Computing Delaunay triangulation...")
points = np.column_stack((df['lon'].values, df['lat'].values))
tri = Delaunay(points)
print(f"Created {len(tri.simplices)} triangles")

# Get coordinates and potential
lons = df['lon'].values
lats = df['lat'].values
potentials = df['potential'].values

print(f"Potential range: {potentials.min():.2e} to {potentials.max():.2e}")

# Geographic bounds
lon_min, lon_max = lons.min(), lons.max()
lat_min, lat_max = lats.min(), lats.max()
lon_range = lon_max - lon_min
lat_range = lat_max - lat_min

# Scale to print dimensions
base_width_cm = 25.0
base_height_cm = 15.0
max_z_cm = 2.0

aspect_ratio = lon_range / lat_range
if aspect_ratio > (base_width_cm / base_height_cm):
    actual_width = base_width_cm
    actual_height = base_width_cm / aspect_ratio
else:
    actual_height = base_height_cm
    actual_width = base_height_cm * aspect_ratio

x_scale = actual_width / lon_range
y_scale = actual_height / lat_range

x_cm = (lons - lon_min) * x_scale
y_cm = (lats - lat_min) * y_scale

# LINEAR Z scaling: 0 to 2cm
z_min, z_max = potentials.min(), potentials.max()
z_cm = (potentials - z_min) / (z_max - z_min) * max_z_cm

print(f"\nPrint dimensions: {actual_width:.1f} × {actual_height:.1f} × {max_z_cm} cm")
print(f"Z aspect: {max_z_cm/actual_width*100:.1f}%")

# Create mesh surface - MONOCHROME
fig = go.Figure(data=[
    go.Mesh3d(
        x=x_cm,
        y=y_cm,
        z=z_cm,
        i=tri.simplices[:, 0],
        j=tri.simplices[:, 1],
        k=tri.simplices[:, 2],
        intensity=z_cm,
        colorscale='Greys',  # Monochrome
        showscale=True,
        colorbar=dict(title="Height (cm)"),
        hovertemplate='X: %{x:.2f}cm<br>Y: %{y:.2f}cm<br>Z: %{z:.3f}cm<extra></extra>',
        lighting=dict(ambient=0.5, diffuse=0.8, specular=0.2),
        flatshading=False
    )
])

fig.update_layout(
    title=f"USA Population Potential - 3D Print Preview<br>" +
          f"<sub>1/d⁴ force (1/d³ potential) | {actual_width:.1f}×{actual_height:.1f}×{max_z_cm}cm | Linear Z scale</sub>",
    scene=dict(
        xaxis=dict(title='Width (cm)'),
        yaxis=dict(title='Depth (cm)'),
        zaxis=dict(title='Height (cm)'),
        aspectmode='data',
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.0)),
        bgcolor='white'
    ),
    width=1400,
    height=900
)

output_path = 'output/usa_3d_print_linear.html'
print(f"\nSaving to {output_path}...")
fig.write_html(output_path)
print(f"✓ Done!")
print(f"\nOpen: {output_path}")
