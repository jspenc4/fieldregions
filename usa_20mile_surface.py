#!/usr/bin/env python3
"""USA 3D surface with 20 mile smoothing."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from lib import io, potential, geometry
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Delaunay
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

log("Loading USA census tracts...")
df = io.load_csv('res/censusTracts.csv')
lons = df['LONGITUDE'].values
lats = df['LATITUDE'].values
weights = df['POPULATION'].values
log(f"  Loaded {len(df):,} tracts")

log("\nCreating Delaunay triangulation...")
points = np.column_stack((lons, lats))
tri = Delaunay(points)
log(f"  Created {len(tri.simplices):,} triangles")

log("\nCalculating triangle centers...")
triangle_centers = []
for triangle in tri.simplices:
    p0 = points[triangle[0]]
    p1 = points[triangle[1]]
    p2 = points[triangle[2]]
    center = (p0 + p1 + p2) / 3.0
    triangle_centers.append(center)
triangle_centers = np.array(triangle_centers)
log(f"  Calculated {len(triangle_centers):,} centers")

center_lons = triangle_centers[:, 0]
center_lats = triangle_centers[:, 1]

log("\nCalculating potential at triangle centers with 20 mile min_distance...")
potentials = potential.calculate_potential_chunked(
    center_lons, center_lats,
    lons, lats, weights,
    geometry.cos_corrected_distance,
    force_exponent=3,
    min_distance_miles=20.0,
    chunk_size=1000
)
log(f"  Potential range: {potentials.min():,.0f} to {potentials.max():,.0f}")

log("\nCreating 3D surface mesh...")
fig = go.Figure(data=[go.Mesh3d(
    x=center_lons,
    y=center_lats,
    z=potentials,
    intensity=potentials,
    colorscale='Viridis',
    showscale=True,
    colorbar=dict(title="Potential"),
    hovertemplate='Lon: %{x:.2f}<br>Lat: %{y:.2f}<br>Potential: %{z:,.0f}<extra></extra>'
)])

fig.update_layout(
    title='USA Population Potential Surface (20 mile smoothing)',
    scene=dict(
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        zaxis_title='Potential',
        aspectmode='manual',
        aspectratio=dict(x=2, y=1, z=0.3)
    ),
    width=1400,
    height=900
)

output_path = 'output/usa_20mile_surface.html'
fig.write_html(output_path)
log(f"\nSaved to {output_path}")
log(f"Open with: open {output_path}")
