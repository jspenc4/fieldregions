#!/usr/bin/env python3
"""
Visualize high-density regions (95th percentile and above).
Show the connected megalopolis structures without trying to trace ridgelines.
"""

import numpy as np
import plotly.graph_objects as go

# Load USA natural data
print("Loading USA natural potential data...")
data = np.loadtxt('output/usa_natural/census_tract_potential.csv', delimiter=',', skiprows=1)
lons = data[:, 0]
lats = data[:, 1]
potentials = data[:, 2]

print(f"Loaded {len(lons):,} points")
print(f"Potential range: {potentials.min():.2e} to {potentials.max():.2e}")

# Find high-potential threshold (95th percentile)
threshold_percentile = 95
threshold = np.percentile(potentials, threshold_percentile)
print(f"\nThreshold ({threshold_percentile}th percentile): {threshold:.2e}")

# Mark high and low potential points
high_mask = potentials >= threshold
low_mask = ~high_mask

print(f"High-potential points: {high_mask.sum():,} ({100*high_mask.sum()/len(lons):.1f}%)")
print(f"Low-potential points: {low_mask.sum():,} ({100*low_mask.sum()/len(lons):.1f}%)")

# Create figure
print("\nCreating visualization...")
fig = go.Figure()

# Add low-potential points (background)
fig.add_trace(go.Scattergeo(
    lon=lons[low_mask],
    lat=lats[low_mask],
    mode='markers',
    marker=dict(
        size=2,
        color='lightgray',
        opacity=0.2
    ),
    name='Low density',
    hoverinfo='skip'
))

# Add high-potential points (highlighted)
fig.add_trace(go.Scattergeo(
    lon=lons[high_mask],
    lat=lats[high_mask],
    mode='markers',
    marker=dict(
        size=4,
        color=np.log10(potentials[high_mask]),
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title='Log(Potential)'),
        cmin=np.log10(threshold),
        cmax=np.log10(potentials.max())
    ),
    name='High density (>95%)',
    hovertemplate='Lon: %{lon:.3f}<br>Lat: %{lat:.3f}<br>Potential: %{marker.color:.2e}<extra></extra>'
))

fig.update_layout(
    title=f'High-Density Urban Regions (>{threshold_percentile}th percentile)',
    geo=dict(
        scope='usa',
        showland=True,
        landcolor='rgb(243, 243, 243)',
        coastlinecolor='rgb(204, 204, 204)',
        projection_type='albers usa'
    ),
    width=1600,
    height=1000,
    showlegend=True
)

output_path = 'output/usa_natural/high_density_regions.html'
print(f"Saving to {output_path}...")
fig.write_html(output_path)
print(f"Done! Open with: open {output_path}")
