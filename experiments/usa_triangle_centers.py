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

# Create triangulation and centers
log('Computing Delaunay triangulation...')
census_points = np.column_stack((df['lon'].values, df['lat'].values))
tri = Delaunay(census_points)
log(f'Created {len(tri.simplices)} triangles')

log('Calculating triangle centers...')
triangle_centers = []
for i, triangle in enumerate(tri.simplices):
    if i % 10000 == 0:
        log(f'  Processing triangle {i}/{len(tri.simplices)}...')
    p0 = census_points[triangle[0]]
    p1 = census_points[triangle[1]]
    p2 = census_points[triangle[2]]
    center = (p0 + p1 + p2) / 3.0
    triangle_centers.append(center)

triangle_centers = np.array(triangle_centers)
log(f'Calculated {len(triangle_centers)} triangle centers')

# Calculate potential at centers
log('\nCalculating potential at triangle centers...')
log('(This will take several hours for USA...)')

def haversine_distance(lat1, lon1, lat2, lon2):
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    a = np.sin(dlat/2)**2 + np.sin(dlon/2)**2 * np.cos(lat1_rad) * np.cos(lat2_rad)
    c = 2 * np.arcsin(np.sqrt(a))
    return 3960 * c

potentials_at_centers = []
for i, center in enumerate(triangle_centers):
    if i % 1000 == 0:
        log(f'  Center {i}/{len(triangle_centers)} ({100*i/len(triangle_centers):.1f}%)')

    center_lon, center_lat = center
    potential = 0.0

    for j in range(len(df)):
        tract_lat = df['lat'].iloc[j]
        tract_lon = df['lon'].iloc[j]
        tract_pop = df['pop'].iloc[j]

        if tract_pop > 0:
            d = haversine_distance(center_lat, center_lon, tract_lat, tract_lon)
            if d > 0:
                contribution = tract_pop / (d ** 3)
                contribution = min(contribution, 500000)
                potential += contribution

    potentials_at_centers.append(potential)

potentials_at_centers = np.array(potentials_at_centers)
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
    title='USA - RAW Height, LOG Color (triangle centers)',
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

output_path = 'output/usa_triangle_centers_raw_logcolor.html'
fig.write_html(output_path)
log(f'\n✓ Saved to {output_path}')
log(f'\nDONE! USA triangle centers visualization complete.')
