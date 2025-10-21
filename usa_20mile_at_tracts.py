#!/usr/bin/env python3
"""Calculate USA potential at census tracts with 20 mile smoothing."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from lib import io, potential, geometry
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

log("Loading USA census tracts...")
df = io.load_csv('res/censusTracts.csv')
lons = df['LONGITUDE'].values
lats = df['LATITUDE'].values
weights = df['POPULATION'].values
log(f"  Loaded {len(df):,} tracts, total population: {weights.sum():,}")

log("\nCalculating potential at census tracts with 20 mile min_distance...")
potentials = potential.calculate_potential_chunked(
    lons, lats,  # Sample AT the tracts
    lons, lats, weights,  # Sources ARE the tracts
    geometry.cos_corrected_distance,
    force_exponent=3,
    min_distance_miles=20.0,
    chunk_size=1000
)
log(f"  Potential range: {potentials.min():,.0f} to {potentials.max():,.0f}")
log(f"  Potential mean: {potentials.mean():,.0f}")

log("\nCreating 3D scatter visualization...")
# Use log scale for z-axis to see structure better
z_values = np.log10(potentials + 1)

fig = go.Figure(data=[go.Scatter3d(
    x=lons,
    y=lats,
    z=z_values,
    mode='markers',
    marker=dict(
        size=1.5,
        color=z_values,
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title="log10(Potential)")
    ),
    text=[f"Lon: {lon:.4f}<br>Lat: {lat:.4f}<br>Pop: {w:,.0f}<br>Potential: {p:,.0f}"
          for lon, lat, w, p in zip(lons, lats, weights, potentials)],
    hoverinfo='text'
)])

fig.update_layout(
    title='USA Population Potential (20 mile smoothing, sampled at census tracts)',
    scene=dict(
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        zaxis_title='log10(Potential)',
        aspectmode='manual',
        aspectratio=dict(x=2, y=1, z=0.3)
    ),
    width=1400,
    height=900
)

output_path = 'output/usa_20mile_at_tracts.html'
fig.write_html(output_path)
log(f"\nSaved to {output_path}")
log(f"Open with: open {output_path}")
