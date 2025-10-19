#!/usr/bin/env python3
"""
Extract ridgeline from population potential surface.
Find the continuous high-density spine of urban regions.
"""

import numpy as np
import pandas as pd
from scipy.spatial import Delaunay
from scipy.ndimage import label
import plotly.graph_objects as go

# Load USA natural data
print("Loading USA natural potential data...")
data = np.loadtxt('output/usa_natural/census_tract_potential.csv', delimiter=',', skiprows=1)
lons = data[:, 0]
lats = data[:, 1]
potentials = data[:, 2]

print(f"Loaded {len(lons):,} points")
print(f"Potential range: {potentials.min():.2e} to {potentials.max():.2e}")

# Build triangulation for connectivity
print("Building triangulation...")
tri = Delaunay(np.column_stack((lons, lats)))

# Build adjacency graph
print("Building adjacency graph...")
adjacency = [set() for _ in range(len(lons))]
for simplex in tri.simplices:
    for i in range(3):
        for j in range(3):
            if i != j:
                adjacency[simplex[i]].add(simplex[j])

# Find high-potential threshold (e.g., top 5%)
threshold_percentile = 95
threshold = np.percentile(potentials, threshold_percentile)
print(f"\nThreshold ({threshold_percentile}th percentile): {threshold:.2e}")

# Mark high-potential points
high_potential_mask = potentials >= threshold
high_potential_indices = np.where(high_potential_mask)[0]
print(f"High-potential points: {len(high_potential_indices):,} ({100*len(high_potential_indices)/len(lons):.1f}%)")

# Find connected components of high-potential regions
print("\nFinding connected components...")
visited = set()
components = []

for start_idx in high_potential_indices:
    if start_idx in visited:
        continue

    # BFS to find connected component
    component = []
    queue = [start_idx]
    visited.add(start_idx)

    while queue:
        current = queue.pop(0)
        component.append(current)

        # Check neighbors
        for neighbor in adjacency[current]:
            if neighbor not in visited and high_potential_mask[neighbor]:
                visited.add(neighbor)
                queue.append(neighbor)

    components.append(component)

# Sort components by size
components.sort(key=len, reverse=True)
print(f"Found {len(components)} connected high-potential regions")
print("Top 10 regions by size:")
for i, comp in enumerate(components[:10]):
    max_pot = potentials[comp].max()
    avg_lat = lats[comp].mean()
    avg_lon = lons[comp].mean()
    print(f"  {i+1}. {len(comp):,} points, max potential: {max_pot:.2e}, center: ({avg_lon:.2f}, {avg_lat:.2f})")

# Extract ridgeline from largest components
# For each component, find the path of local maxima
print("\nExtracting ridgelines from top components...")

ridgelines = []
for comp_idx, component in enumerate(components[:5]):  # Top 5 regions
    if len(component) < 10:
        break

    # Sort points by potential
    comp_array = np.array(component)
    comp_potentials = potentials[comp_array]
    sorted_indices = np.argsort(comp_potentials)[::-1]

    # Start from highest point
    ridgeline = [comp_array[sorted_indices[0]]]

    # Greedily follow highest neighbors
    current = ridgeline[0]
    visited_ridge = {current}

    while True:
        # Find unvisited neighbors in the component
        candidates = []
        for neighbor in adjacency[current]:
            if neighbor in visited_ridge:
                continue
            if neighbor in comp_array:
                candidates.append(neighbor)

        if not candidates:
            break

        # Pick highest potential neighbor
        best = max(candidates, key=lambda x: potentials[x])
        ridgeline.append(best)
        visited_ridge.add(best)
        current = best

        # Don't make ridgeline too long
        if len(ridgeline) > 100:
            break

    ridgelines.append(ridgeline)
    print(f"  Region {comp_idx+1}: ridgeline with {len(ridgeline)} points")

# Visualize ridgelines on map
print("\nCreating visualization...")
fig = go.Figure()

# Add all points as scatter
fig.add_trace(go.Scatter(
    x=lons,
    y=lats,
    mode='markers',
    marker=dict(
        size=2,
        color=np.log10(potentials + 1),
        colorscale='Viridis',
        opacity=0.3,
        showscale=True,
        colorbar=dict(title='Log(Potential)')
    ),
    name='All points',
    hoverinfo='skip'
))

# Add ridgelines
colors = ['red', 'orange', 'yellow', 'cyan', 'magenta']
for i, ridgeline in enumerate(ridgelines):
    ridge_lons = lons[ridgeline]
    ridge_lats = lats[ridgeline]
    fig.add_trace(go.Scatter(
        x=ridge_lons,
        y=ridge_lats,
        mode='lines+markers',
        line=dict(color=colors[i % len(colors)], width=3),
        marker=dict(size=6, color=colors[i % len(colors)]),
        name=f'Ridge {i+1} ({len(ridgeline)} pts)'
    ))

fig.update_layout(
    title=f'Population Potential Ridgelines (>{threshold_percentile}th percentile)',
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    width=1400,
    height=900,
    showlegend=True
)

output_path = 'output/usa_natural/ridgelines.html'
print(f"Saving to {output_path}...")
fig.write_html(output_path)
print(f"Done! Open with: open {output_path}")

# Save ridgeline data
print("\nSaving ridgeline coordinates...")
for i, ridgeline in enumerate(ridgelines):
    ridge_data = np.column_stack((lons[ridgeline], lats[ridgeline], potentials[ridgeline]))
    output_csv = f'output/usa_natural/ridgeline_{i+1}.csv'
    np.savetxt(output_csv, ridge_data, delimiter=',',
               header='longitude,latitude,potential', comments='',
               fmt='%.6f,%.6f,%.8e')
    print(f"  Ridge {i+1}: {output_csv}")
