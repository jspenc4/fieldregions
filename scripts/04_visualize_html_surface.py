#!/usr/bin/env python3
"""
Visualize USA 1/d³ potential using go.Surface (interpolated grid).

Input:  output/usa/triangle_centers_d3_potential.csv
Output: output/usa/preview_surface_8pct_z.html

Visualization:
- Interpolated regular grid (smoother, no triangle artifacts)
- 8% Z aspect ratio (2cm height / 25cm width equivalent)
- Linear Z scale
- Monochrome grayscale
- Lat/long axis labels
- Interactive drag/rotate/zoom
"""

import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import griddata
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

# Create regular grid for interpolation
print("Creating regular grid...")
# Use moderate resolution for good performance
grid_resolution_lon = 400
grid_resolution_lat = 200

lon_grid = np.linspace(lons.min(), lons.max(), grid_resolution_lon)
lat_grid = np.linspace(lats.min(), lats.max(), grid_resolution_lat)
lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

# Interpolate potential onto regular grid
print("Interpolating to regular grid (this may take a moment)...")
points = np.column_stack((lons, lats))
potential_mesh = griddata(points, potentials, (lon_mesh, lat_mesh), method='linear')

# Handle NaN values (outside convex hull)
potential_mesh = np.nan_to_num(potential_mesh, nan=potentials.min())

print(f"Grid: {grid_resolution_lat} × {grid_resolution_lon}")

# Calculate Z aspect ratio: 8% (2cm / 25cm)
z_aspect = 0.08

# Geographic bounds
lon_range = lons.max() - lons.min()
lat_range = lats.max() - lats.min()

# Scale Z to 8% of width
pot_min, pot_max = potentials.min(), potentials.max()
z_normalized = (potential_mesh - pot_min) / (pot_max - pot_min)
z_scaled = z_normalized * (lon_range * z_aspect)

print(f"\nScaling:")
print(f"  Geographic: {lon_range:.1f}° × {lat_range:.1f}°")
print(f"  Z range: 0 to {np.nanmax(z_scaled):.2f}° ({z_aspect*100:.1f}% of width)")
print(f"  Z aspect ratio: {z_aspect*100:.1f}%")

# Create surface
fig = go.Figure(data=[
    go.Surface(
        x=lon_mesh,
        y=lat_mesh,
        z=z_scaled,
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
        )
    )
])

fig.update_layout(
    title=dict(
        text="USA Population Potential - Interpolated Surface<br>" +
             f"<sub>1/d³ potential | {z_aspect*100:.1f}% Z aspect | Linear scale | {grid_resolution_lat}×{grid_resolution_lon} grid</sub>",
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

output_path = Path('output/usa/preview_surface_8pct_z.html')
print(f"\nSaving to {output_path}...")
fig.write_html(str(output_path))
print(f"✓ Done! Open {output_path}")
