#!/usr/bin/env python3
"""
Generate USA 1/d³ potential preview scaled for 3D printing.
Uses triangle centers from Delaunay triangulation of census tracts.

Print specs: 25cm × 15cm base, 2cm max height, monochrome
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Delaunay
import sys
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

# Load USA data
log('Loading USA census tract data...')
df = pd.read_csv('output/census_potential_d3_capped.csv',
                 names=['type', 'pop', 'lat', 'lon', 'potential'])

log(f'Loaded {len(df)} census tract centroids')

# Create triangulation and centers
log('Computing Delaunay triangulation...')
census_points = np.column_stack((df['lon'].values, df['lat'].values))
tri = Delaunay(census_points)
log(f'Created {len(tri.simplices)} triangles')

log('Calculating triangle centers...')
triangle_centers = []
for i, triangle in enumerate(tri.simplices):
    if i % 10000 == 0:
        log(f'  Triangle {i}/{len(tri.simplices)}...')
    p0 = census_points[triangle[0]]
    p1 = census_points[triangle[1]]
    p2 = census_points[triangle[2]]
    center = (p0 + p1 + p2) / 3.0
    triangle_centers.append(center)

triangle_centers = np.array(triangle_centers)
log(f'Calculated {len(triangle_centers)} triangle centers')

# Calculate potential at centers
log('\nCalculating 1/d³ potential at triangle centers...')

tract_lons = df['lon'].values
tract_lats = df['lat'].values
tract_pops = df['pop'].values

avg_lat = np.mean(tract_lats)
cos_avg_lat = np.cos(np.radians(avg_lat))

potentials_at_centers = np.zeros(len(triangle_centers))

chunk_size = 1000
num_chunks = (len(triangle_centers) + chunk_size - 1) // chunk_size

for chunk_idx in range(num_chunks):
    start_idx = chunk_idx * chunk_size
    end_idx = min(start_idx + chunk_size, len(triangle_centers))

    if chunk_idx % 10 == 0:
        pct = 100 * start_idx / len(triangle_centers)
        log(f'  Processing {start_idx}/{len(triangle_centers)} ({pct:.1f}%)')

    centers_chunk = triangle_centers[start_idx:end_idx]
    center_lons = centers_chunk[:, 0]
    center_lats = centers_chunk[:, 1]

    dlon = (center_lons[:, np.newaxis] - tract_lons[np.newaxis, :]) * cos_avg_lat
    dlat = center_lats[:, np.newaxis] - tract_lats[np.newaxis, :]

    distances = np.sqrt(dlon**2 + dlat**2) * 69.0  # miles
    distances = np.maximum(distances, 0.001)

    # 1/d³ potential
    contributions = tract_pops[np.newaxis, :] / (distances ** 3)
    contributions = np.minimum(contributions, 500000)  # cap

    potentials_chunk = np.sum(contributions, axis=1)
    potentials_at_centers[start_idx:end_idx] = potentials_chunk

log(f'Potential range: {potentials_at_centers.min():.0f} to {potentials_at_centers.max():.0f}')

# Scale for 3D printing
log('\nScaling for 3D print...')

lons = triangle_centers[:, 0]
lats = triangle_centers[:, 1]

# Geographic bounds
lon_min, lon_max = lons.min(), lons.max()
lat_min, lat_max = lats.min(), lats.max()
lon_range = lon_max - lon_min
lat_range = lat_max - lat_min

log(f'Geographic bounds: Lon [{lon_min:.1f}, {lon_max:.1f}], Lat [{lat_min:.1f}, {lat_max:.1f}]')

# Scale to print dimensions (cm)
base_width_cm = 25.0
base_height_cm = 15.0
max_z_cm = 2.0

# Preserve aspect ratio
aspect_ratio = lon_range / lat_range
if aspect_ratio > (base_width_cm / base_height_cm):
    # Width-constrained
    actual_width = base_width_cm
    actual_height = base_width_cm / aspect_ratio
else:
    # Height-constrained
    actual_height = base_height_cm
    actual_width = base_height_cm * aspect_ratio

x_scale = actual_width / lon_range
y_scale = actual_height / lat_range

x_cm = (lons - lon_min) * x_scale
y_cm = (lats - lat_min) * y_scale

# Normalize Z to 0-2cm
z_min, z_max = potentials_at_centers.min(), potentials_at_centers.max()
z_cm = (potentials_at_centers - z_min) / (z_max - z_min) * max_z_cm

log(f'Print dimensions: {actual_width:.1f}cm × {actual_height:.1f}cm × {max_z_cm}cm')
log(f'Z aspect: {max_z_cm/actual_width*100:.1f}% (height/width)')

# Create triangulation for surface
log('\nCreating 3D surface...')
fig = go.Figure(data=[
    go.Mesh3d(
        x=x_cm,
        y=y_cm,
        z=z_cm,
        i=tri.simplices[:, 0],
        j=tri.simplices[:, 1],
        k=tri.simplices[:, 2],
        intensity=z_cm,
        colorscale='Greys',
        showscale=True,
        colorbar=dict(title="Height (cm)", titleside="right"),
        hovertemplate='X: %{x:.2f}cm<br>Y: %{y:.2f}cm<br>Z: %{z:.3f}cm<extra></extra>',
        lighting=dict(ambient=0.5, diffuse=0.8, specular=0.2, roughness=0.5),
        flatshading=False
    )
])

fig.update_layout(
    title=dict(
        text=f"USA Population Potential - 3D Print Preview<br>" +
             f"<sub>1/d⁴ force (1/d³ potential) | {actual_width:.1f}×{actual_height:.1f}×{max_z_cm}cm | Monochrome</sub>",
        font=dict(size=16)
    ),
    scene=dict(
        xaxis=dict(title='Width (cm)', range=[0, actual_width]),
        yaxis=dict(title='Depth (cm)', range=[0, actual_height]),
        zaxis=dict(title='Height (cm)', range=[0, max_z_cm]),
        aspectmode='data',
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.0)),
        bgcolor='white'
    ),
    width=1400,
    height=900,
    paper_bgcolor='white'
)

output_path = 'output/usa_3d_print_preview.html'
log(f'\nSaving to {output_path}...')
fig.write_html(output_path)
log(f'✓ Done! Open {output_path} to view')

print()
print("="*70)
print(f"✓ USA 3D print preview ready")
print("="*70)
print(f"Dimensions: {actual_width:.1f} × {actual_height:.1f} × {max_z_cm} cm")
print(f"Triangle mesh: {len(tri.simplices):,} faces")
print(f"Open: {output_path}")
print("="*70)
