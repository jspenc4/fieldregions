#!/usr/bin/env python3
"""SF Bay Area - sample at tracts with 1 mile min_distance."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from lib import io, potential, geometry
import plotly.graph_objects as go

print("Loading SF Bay tracts...")
df = io.load_csv('res/tracts_sf_bay.csv')
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
fig = go.Figure(data=[go.Mesh3d(
    x=lons,
    y=lats,
    z=potentials,
    intensity=potentials,
    colorscale='Viridis',
    showscale=True
)])

fig.update_layout(
    title='SF Bay Population Potential (1 mile smoothing)',
    scene=dict(
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        zaxis_title='Potential',
        aspectmode='manual',
        aspectratio=dict(x=1.5, y=1, z=0.3)
    ),
    width=1200,
    height=800
)

output = 'output/sf_1mile_simple.html'
fig.write_html(output)
print(f"\nSaved: {output}")
