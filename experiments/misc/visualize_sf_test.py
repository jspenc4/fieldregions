#!/usr/bin/env python3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Delaunay
from lib import io, potential

# Load SF Bay data
print('Loading SF Bay data...')
df = io.load_csv('res/tracts_sf_bay.csv')
lons = df['LONGITUDE'].values
lats = df['LATITUDE'].values
weights = df['POPULATION'].values
avg_lat = np.mean(lats)

# Calculate potential at census tracts (excluding self)
print('Calculating potential...')
potentials = potential.calculate_potential_chunked(
    lons, lats, lons, lats, weights, avg_lat, force_exponent=3
)

print(f'Potential range: {potentials.min():.0f} to {potentials.max():.0f}')

# Create triangulation for visualization
print('Creating triangulation...')
points = np.column_stack((lons, lats))
tri = Delaunay(points)

# Create 3D mesh
z_raw = potentials
color_log = np.log10(potentials + 1)

fig = go.Figure(data=[go.Mesh3d(
    x=lons, y=lats, z=z_raw,
    i=tri.simplices[:,0],
    j=tri.simplices[:,1],
    k=tri.simplices[:,2],
    colorscale='Viridis',
    intensity=color_log,
    colorbar=dict(title='log₁₀(Potential)'),
    opacity=1.0,
    hovertemplate='Lon: %{x:.3f}<br>Lat: %{y:.3f}<br>Potential: %{z:.0f}<extra></extra>'
)])

# Aspect ratio
cos_avg_lat = np.cos(np.radians(avg_lat))
lon_range = lons.max() - lons.min()
lat_range = lats.max() - lats.min()
aspect_x = lon_range * cos_avg_lat / lat_range
z_aspect = 0.3

fig.update_layout(
    title='SF Bay Area - Population Potential (self-contribution excluded)',
    scene=dict(
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        zaxis_title='Potential',
        camera=dict(eye=dict(x=1.5, y=-1.0, z=1.2)),
        aspectmode='manual',
        aspectratio=dict(x=aspect_x, y=1.0, z=z_aspect)
    ),
    width=1400, height=900
)

output_path = 'output/sf_bay_test.html'
fig.write_html(output_path)
print(f'Saved to {output_path}')
