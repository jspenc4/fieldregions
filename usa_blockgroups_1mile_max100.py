#!/usr/bin/env python3
"""USA Block Groups - 1 mile min, 100 mile max distance."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from lib import io, potential, geometry
import plotly.graph_objects as go
import numpy as np
import time

print("Loading USA block groups...")
df = io.load_csv('res/censusBlockGroups.csv')

# Filter to continental US only (exclude Alaska, Hawaii, territories)
df = df[(df['LATITUDE'] >= 25) & (df['LATITUDE'] <= 50) & (df['LONGITUDE'] >= -125)]
print(f"  {len(df)} block groups (continental US only)")

lons = df['LONGITUDE'].values
lats = df['LATITUDE'].values
weights = df['POPULATION'].values

print("\nCalculating potential (1 mile min, 100 mile max distance)...")
print(f"  Sampling at all {len(lons):,} block group locations")
start_time = time.time()

potentials = potential.calculate_potential_chunked(
    lons, lats,  # Sample at all block groups
    lons, lats, weights,  # Source is all block groups
    geometry.haversine_distance,
    force_exponent=3,
    min_distance_miles=1.0,
    max_distance_miles=100.0,
    n_jobs=4
)

elapsed = time.time() - start_time
print(f"  Completed in {elapsed/60:.1f} minutes")
print(f"  Range: {potentials.min():,.0f} to {potentials.max():,.0f}")

print("\nCreating 3D surface...")

# Calculate aspect ratio
center_lat = np.mean(lats)
lon_span = lons.max() - lons.min()
lat_span = lats.max() - lats.min()
lon_to_lat_ratio = np.cos(np.radians(center_lat))

# Normalize aspect ratios
avg_horiz_span = (lon_span * lon_to_lat_ratio + lat_span) / 2
max_horiz = max(lon_span * lon_to_lat_ratio, lat_span)

aspect_x = (lon_span * lon_to_lat_ratio) / max_horiz
aspect_y = lat_span / max_horiz
aspect_z = (0.08 * avg_horiz_span) / max_horiz

# Use log scale for color
log_potentials = np.log10(potentials + 1)

fig = go.Figure(data=[go.Mesh3d(
    x=lons,
    y=lats,
    z=potentials,
    intensity=log_potentials,
    colorscale='Viridis',
    showscale=True,
    colorbar=dict(title="log₁₀(Potential)")
)])

fig.update_layout(
    title='USA Block Groups Population Potential (1 mile min, 100 mile max)',
    scene=dict(
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        zaxis_title='Potential',
        aspectmode='manual',
        aspectratio=dict(x=aspect_x, y=aspect_y, z=aspect_z),
        camera=dict(
            eye=dict(x=1.5, y=1.5, z=1.2),
            center=dict(x=0, y=0, z=0)
        )
    ),
    width=1200,
    height=900
)

print(f"  Aspect ratio: x={aspect_x:.4f}, y={aspect_y:.4f}, z={aspect_z:.4f}")

output = 'output/usa_blockgroups_1mile_max100.html'
fig.write_html(output)
print(f"\nSaved: {output}")
