#!/usr/bin/env python3
"""California - sample at tracts with 1 mile min_distance."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from lib import io, potential, geometry
import plotly.graph_objects as go

print("Loading California tracts...")
df = io.load_csv('res/tracts_california.csv')
lons = df['LONGITUDE'].values
lats = df['LATITUDE'].values
weights = df['POPULATION'].values
print(f"  {len(df)} tracts")

print("\nCalculating potential (1 mile min_distance)...")
potentials = potential.calculate_potential_chunked(
    lons, lats,  # Sample at tracts
    lons, lats, weights,  # Source is tracts
    geometry.haversine_distance,
    force_exponent=3,
    min_distance_miles=1.0
)
print(f"  Range: {potentials.min():,.0f} to {potentials.max():,.0f}")

print("\nCreating 3D surface...")
import numpy as np

# Calculate aspect ratio: correct for latitude so 1 degree lon = 1 degree lat in miles
center_lat = np.mean(lats)
lon_span = lons.max() - lons.min()
lat_span = lats.max() - lats.min()

# At center latitude, 1 degree longitude = cos(lat) * 69 miles
# 1 degree latitude = 69.172 miles
# So aspect ratio lon:lat should be cos(center_lat) : 1
lon_to_lat_ratio = np.cos(np.radians(center_lat))

# Z aspect: 4% of the average horizontal span
avg_horiz_span = (lon_span * lon_to_lat_ratio + lat_span) / 2
z_span = potentials.max() - potentials.min()
z_aspect = 0.04 * avg_horiz_span / z_span if z_span > 0 else 0.04

fig = go.Figure(data=[go.Mesh3d(
    x=lons,
    y=lats,
    z=potentials,
    intensity=potentials,
    colorscale='Viridis',
    showscale=True
)])

fig.update_layout(
    title='California Population Potential (1 mile smoothing)',
    scene=dict(
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        zaxis_title='Potential',
        aspectmode='manual',
        aspectratio=dict(x=lon_span * lon_to_lat_ratio, y=lat_span, z=z_span * z_aspect)
    ),
    width=1200,
    height=900
)

print(f"  Aspect ratio: lon={lon_span * lon_to_lat_ratio:.2f}, lat={lat_span:.2f}, z={z_span * z_aspect:.2f}")

output = 'output/ca_1mile_simple.html'
fig.write_html(output)
print(f"\nSaved: {output}")
