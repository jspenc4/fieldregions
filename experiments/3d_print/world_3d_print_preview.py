#!/usr/bin/env python3
"""
Generate world 1/d³ potential preview for 3D printing.
Linear Z scale: 0-2cm, monochrome, 25×15cm base.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

print("Loading world 1/d³ potential data...")
csv_path = Path.home() / "git" / "gridded" / "res" / "potential_1_over_d3_selfexclude" / "raw_potential.csv"

df = pd.read_csv(csv_path, names=['type', 'pop', 'lat', 'lon', 'potential'])
print(f"Loaded {len(df)} grid points")

# Create grid
unique_lats = sorted(df['lat'].unique(), reverse=True)
unique_lons = sorted(df['lon'].unique())
nrows, ncols = len(unique_lats), len(unique_lons)

print(f"Grid: {nrows} × {ncols}")

lon_grid, lat_grid = np.meshgrid(unique_lons, unique_lats)
df_sorted = df.sort_values(['lat', 'lon'], ascending=[False, True])
potential_grid = df_sorted['potential'].values.reshape(nrows, ncols)

print(f"Potential range: {potential_grid.min():.2e} to {potential_grid.max():.2e}")

# Geographic bounds
lon_min, lon_max = unique_lons[0], unique_lons[-1]
lat_min, lat_max = unique_lats[-1], unique_lats[0]
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

x_cm = (lon_grid - lon_min) * x_scale
y_cm = (lat_grid - lat_min) * y_scale

# LINEAR Z scaling: 0 to 2cm
z_min, z_max = potential_grid.min(), potential_grid.max()
z_cm = (potential_grid - z_min) / (z_max - z_min) * max_z_cm

print(f"\nPrint dimensions: {actual_width:.1f} × {actual_height:.1f} × {max_z_cm} cm")
print(f"Z aspect: {max_z_cm/actual_width*100:.1f}%")

# Create surface - MONOCHROME
fig = go.Figure(data=[
    go.Surface(
        x=x_cm,
        y=y_cm,
        z=z_cm,
        colorscale='Greys',  # Monochrome
        showscale=True,
        colorbar=dict(title="Height (cm)"),
        hovertemplate='X: %{x:.2f}cm<br>Y: %{y:.2f}cm<br>Z: %{z:.3f}cm<extra></extra>',
        lighting=dict(ambient=0.5, diffuse=0.8, specular=0.2)
    )
])

fig.update_layout(
    title=f"World Population Potential - 3D Print Preview<br>" +
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

output_path = 'output/world_3d_print_preview.html'
print(f"\nSaving to {output_path}...")
fig.write_html(output_path)
print(f"✓ Done!")
print(f"\nOpen: {output_path}")
