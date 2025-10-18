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

# Load USA data
log('Loading USA data...')
df = pd.read_csv('output/census_potential_d3_capped.csv',
                 names=['type', 'pop', 'lat', 'lon', 'potential'])

log(f'Loaded {len(df)} census tract centroids')

# Extract arrays
tract_lons = df['lon'].values
tract_lats = df['lat'].values
tract_pops = df['pop'].values

# Average latitude for scaling
avg_lat = np.mean(tract_lats)
cos_avg_lat = np.cos(np.radians(avg_lat))

# Get bounds and expand for hexagonal grid
lon_min, lon_max = tract_lons.min(), tract_lons.max()
lat_min, lat_max = tract_lats.min(), tract_lats.max()

# Expand bounds by 10% on each side
lon_margin = (lon_max - lon_min) * 0.10
lat_margin = (lat_max - lat_min) * 0.10

lon_min_expanded = lon_min - lon_margin
lon_max_expanded = lon_max + lon_margin
lat_min_expanded = lat_min - lat_margin
lat_max_expanded = lat_max + lat_margin

log(f'\nOriginal bounds: lon [{lon_min:.2f}, {lon_max:.2f}], lat [{lat_min:.2f}, {lat_max:.2f}]')
log(f'Expanded bounds: lon [{lon_min_expanded:.2f}, {lon_max_expanded:.2f}], lat [{lat_min_expanded:.2f}, {lat_max_expanded:.2f}]')

# Create hexagonal grid
log('\nCreating hexagonal grid...')
spacing = 0.5  # degrees
hex_points = []

row = 0
lat = lat_min_expanded
while lat <= lat_max_expanded:
    lon = lon_min_expanded
    if row % 2 == 1:
        lon += spacing * 0.5

    while lon <= lon_max_expanded:
        hex_points.append([lon, lat])
        lon += spacing

    lat += spacing * np.sqrt(3) / 2
    row += 1

hex_points = np.array(hex_points)
log(f'Created hexagonal grid with {len(hex_points)} points')

# Filter out grid points that are too close to census tracts
log('\nFiltering grid points too close to census tracts...')
min_distance_threshold = 0.1  # degrees

# For each hex point, calculate distance to nearest census tract
distances_to_tracts = []
for i, hex_pt in enumerate(hex_points):
    if i % 1000 == 0:
        log(f'  Checking grid point {i}/{len(hex_points)}...')
    dlon = (hex_pt[0] - tract_lons) * cos_avg_lat
    dlat = hex_pt[1] - tract_lats
    dists = np.sqrt(dlon**2 + dlat**2)
    min_dist = dists.min()
    distances_to_tracts.append(min_dist)

distances_to_tracts = np.array(distances_to_tracts)
keep_mask = distances_to_tracts >= min_distance_threshold

hex_points_filtered = hex_points[keep_mask]
log(f'Kept {len(hex_points_filtered)} grid points after filtering (removed {(~keep_mask).sum()} points)')

# Combine census tracts with filtered hex grid
log('\nCombining census tracts with hex grid...')
all_points = np.vstack([np.column_stack((tract_lons, tract_lats)), hex_points_filtered])
log(f'Total points: {len(all_points)} ({len(tract_lons)} census tracts + {len(hex_points_filtered)} hex grid)')

# Calculate potential at ALL POINTS (excluding 2 closest steps)
log('\nCalculating potential at all points (EXCLUDING 2 closest steps)...')

potentials_at_grid = np.zeros(len(all_points))

# Process in chunks to manage memory
chunk_size = 1000
num_chunks = (len(all_points) + chunk_size - 1) // chunk_size

for chunk_idx in range(num_chunks):
    start_idx = chunk_idx * chunk_size
    end_idx = min(start_idx + chunk_size, len(all_points))

    if chunk_idx % 10 == 0:
        pct = 100 * start_idx / len(all_points)
        log(f'  Processing points {start_idx}/{len(all_points)} ({pct:.1f}%)')

    # Get chunk of points
    chunk_lons = all_points[start_idx:end_idx, 0]
    chunk_lats = all_points[start_idx:end_idx, 1]

    # Vectorized distance calculation to ALL census tracts
    dlon = (chunk_lons[:, np.newaxis] - tract_lons[np.newaxis, :]) * cos_avg_lat
    dlat = chunk_lats[:, np.newaxis] - tract_lats[np.newaxis, :]

    # Euclidean distance in miles
    distances = np.sqrt(dlon**2 + dlat**2) * 69.0

    # For each grid point, find its 2 closest census tracts and exclude them
    sorted_distances = np.sort(distances, axis=1)
    # The threshold is the 3rd smallest distance (index 2)
    threshold_distances = sorted_distances[:, 2:3]  # shape (chunk_size, 1)

    # Create mask: True where we should INCLUDE the contribution
    # Exclude the 2 closest AND exclude anything beyond 50 miles
    mask = (distances >= threshold_distances) & (distances <= 50.0)

    # Avoid division by zero
    distances = np.maximum(distances, 0.001)

    # Calculate contributions: pop / d^3, capped at 500k
    contributions = tract_pops[np.newaxis, :] / (distances ** 3)
    contributions = np.minimum(contributions, 500000)

    # Zero out the excluded contributions
    contributions = contributions * mask

    # Sum contributions for each grid point in chunk
    potentials_chunk = np.sum(contributions, axis=1)
    potentials_at_grid[start_idx:end_idx] = potentials_chunk

log(f'\nPotential range: {potentials_at_grid.min():.0f} to {potentials_at_grid.max():.0f}')

# Zero out values under 1000
log('Zeroing out values under 1000...')
potentials_at_grid[potentials_at_grid < 1000] = 0
log(f'After zeroing: range {potentials_at_grid.min():.0f} to {potentials_at_grid.max():.0f}')

# Create triangulation of all points
log('\nCreating Delaunay triangulation of all points...')
tri = Delaunay(all_points)
log(f'Created {len(tri.simplices)} triangles')

# Raw height, log color
z_raw = potentials_at_grid
color_log = np.log10(potentials_at_grid + 1)

fig = go.Figure(data=[go.Mesh3d(
    x=all_points[:,0],
    y=all_points[:,1],
    z=z_raw,
    i=tri.simplices[:,0],
    j=tri.simplices[:,1],
    k=tri.simplices[:,2],
    colorscale='Viridis',
    intensity=color_log,
    colorbar=dict(title='log₁₀(Potential)<br>(color only)'),
    opacity=1.0,
    hovertemplate='Lon: %{x:.2f}<br>Lat: %{y:.2f}<br>Potential: %{z:.0f}<extra></extra>'
)])

# Aspect ratio with 4% z_aspect
lon_range = lon_max_expanded - lon_min_expanded
lat_range = lat_max_expanded - lat_min_expanded
aspect_x = lon_range * cos_avg_lat / lat_range

z_aspect = 0.04
log(f'Using z_aspect = {z_aspect:.3f}')

fig.update_layout(
    title='USA - Excluding 2 Closest Steps (Hex Grid, 4% Z, 50mi cutoff, z>1000)',
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

output_path = 'output/usa_exclude_2_steps.html'
fig.write_html(output_path)
log(f'\n✓ Saved to {output_path}')
log(f'\nDONE! USA visualization (excluding 2 closest steps) complete.')
