#!/usr/bin/env python3
"""USA - sample at tracts with 1 mile min_distance."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from lib import io, potential, geometry
import plotly.graph_objects as go

print("Loading USA tracts...")
df = io.load_csv('res/censusTracts.csv')
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
    min_distance_miles=1.0,
    n_jobs=-1  # Use all cores
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

# Z aspect: height should be 4% of average horizontal span
# Normalize aspect ratios so largest horizontal dimension = 1.0
avg_horiz_span = (lon_span * lon_to_lat_ratio + lat_span) / 2
max_horiz = max(lon_span * lon_to_lat_ratio, lat_span)

aspect_x = (lon_span * lon_to_lat_ratio) / max_horiz
aspect_y = lat_span / max_horiz
aspect_z = (0.08 * avg_horiz_span) / max_horiz

# Use log scale for color intensity
log_potentials = np.log10(potentials + 1)  # +1 to avoid log(0)

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
    title='USA Population Potential (1 mile smoothing)',
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

output = 'output/usa_1mile_simple.html'
fig.write_html(output)
print(f"\nSaved: {output}")
