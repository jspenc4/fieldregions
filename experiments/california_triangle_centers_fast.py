#!/usr/bin/env python3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Delaunay
import sys
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

# Load California data
log('Loading California data...')
df = pd.read_csv('output/california_potential_d3_capped.csv',
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
    if i % 5000 == 0:
        log(f'  Processing triangle {i}/{len(tri.simplices)}...')
    p0 = census_points[triangle[0]]
    p1 = census_points[triangle[1]]
    p2 = census_points[triangle[2]]
    center = (p0 + p1 + p2) / 3.0
    triangle_centers.append(center)

triangle_centers = np.array(triangle_centers)
log(f'Calculated {len(triangle_centers)} triangle centers')

# Calculate potential at centers using VECTORIZED operations
log('\nCalculating potential at triangle centers (FAST VERSION)...')
log('Using simple Euclidean distance with latitude correction')

# Pre-compute arrays
tract_lons = df['lon'].values
tract_lats = df['lat'].values
tract_pops = df['pop'].values

# Average latitude for scaling
avg_lat = np.mean(tract_lats)
cos_avg_lat = np.cos(np.radians(avg_lat))

potentials_at_centers = np.zeros(len(triangle_centers))

# Process in chunks to manage memory
chunk_size = 1000
num_chunks = (len(triangle_centers) + chunk_size - 1) // chunk_size

for chunk_idx in range(num_chunks):
    start_idx = chunk_idx * chunk_size
    end_idx = min(start_idx + chunk_size, len(triangle_centers))

    if chunk_idx % 5 == 0:
        pct = 100 * start_idx / len(triangle_centers)
        log(f'  Processing centers {start_idx}/{len(triangle_centers)} ({pct:.1f}%)')

    # Get chunk of centers
    centers_chunk = triangle_centers[start_idx:end_idx]

    # Vectorized distance calculation
    center_lons = centers_chunk[:, 0]
    center_lats = centers_chunk[:, 1]

    # Broadcast to get all pairwise distances
    dlon = (center_lons[:, np.newaxis] - tract_lons[np.newaxis, :]) * cos_avg_lat
    dlat = center_lats[:, np.newaxis] - tract_lats[np.newaxis, :]

    # Euclidean distance in scaled (lon, lat) space
    # Multiply by ~69 miles per degree to get approximate miles
    distances = np.sqrt(dlon**2 + dlat**2) * 69.0

    # Avoid division by zero
    distances = np.maximum(distances, 0.001)

    # Calculate contributions: pop / d^3, capped at 500k
    contributions = tract_pops[np.newaxis, :] / (distances ** 3)
    contributions = np.minimum(contributions, 500000)

    # Sum contributions for each center in chunk
    potentials_chunk = np.sum(contributions, axis=1)
    potentials_at_centers[start_idx:end_idx] = potentials_chunk

log(f'\nPotential range: {potentials_at_centers.min():.0f} to {potentials_at_centers.max():.0f}')

# Raw height, log color
z_raw = potentials_at_centers
color_log = np.log10(potentials_at_centers + 1)

# Triangulate centers
log('\nCreating visualization mesh...')
tri_centers = Delaunay(triangle_centers)

fig = go.Figure(data=[go.Mesh3d(
    x=triangle_centers[:,0],
    y=triangle_centers[:,1],
    z=z_raw,
    i=tri_centers.simplices[:,0],
    j=tri_centers.simplices[:,1],
    k=tri_centers.simplices[:,2],
    colorscale='Viridis',
    intensity=color_log,
    colorbar=dict(title='log₁₀(Potential)<br>(color only)'),
    opacity=1.0,
    hovertemplate='Lon: %{x:.2f}<br>Lat: %{y:.2f}<br>Potential: %{z:.0f}<extra></extra>'
)])

# Aspect ratio - scale z to match Bay Area proportions
avg_lat = triangle_centers[:,1].mean()
cos_avg_lat = np.cos(np.radians(avg_lat))
lon_range = triangle_centers[:,0].max() - triangle_centers[:,0].min()
lat_range = triangle_centers[:,1].max() - triangle_centers[:,1].min()
aspect_x = lon_range * cos_avg_lat / lat_range

# Scale z_aspect proportional to region size (match Bay Area)
z_aspect = 0.3 * (0.79 / lat_range)
log(f'Using z_aspect = {z_aspect:.3f}')

fig.update_layout(
    title='California - RAW Height, LOG Color (triangle centers - FAST)',
    scene=dict(
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        zaxis_title='Potential (raw height)',
        camera=dict(eye=dict(x=1.5, y=-1.0, z=1.2)),
        aspectmode='manual',
        aspectratio=dict(x=aspect_x, y=1.0, z=z_aspect)
    ),
    width=1400,
    height=900
)

output_path = 'output/california_triangle_centers_fast.html'
fig.write_html(output_path)
log(f'\n✓ Saved to {output_path}')
log(f'\nDONE! California triangle centers visualization complete.')
