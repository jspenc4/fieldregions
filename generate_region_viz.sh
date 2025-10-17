#!/bin/bash
# Generate visualizations for a specific region with 2-mile exclusion

REGION=$1
INPUT_CSV=$2

if [ -z "$REGION" ] || [ -z "$INPUT_CSV" ]; then
    echo "Usage: ./generate_region_viz.sh <region_name> <input_csv>"
    echo "Example: ./generate_region_viz.sh california res/tracts_california.csv"
    exit 1
fi

echo "Generating visualizations for $REGION..."

# Create region-specific calculation script
cat > /tmp/calc_${REGION}.py << 'EOFPYTHON'
#!/usr/bin/env python3
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path
from datetime import datetime
import sys

region_name = sys.argv[1]
input_csv = sys.argv[2]

print(f"Processing {region_name}...")

# Load census data
df = pd.read_csv(input_csv)
print(f"Loaded {len(df):,} census tracts")

# Triangulate
census_points = np.column_stack((df['LONGITUDE'].values, df['LATITUDE'].values))
tri = Delaunay(census_points)
print(f"Created {len(tri.simplices):,} triangles")

# Calculate centers
triangle_centers = []
for triangle_idx in tri.simplices:
    p0, p1, p2 = census_points[triangle_idx]
    triangle_centers.append((p0 + p1 + p2) / 3.0)
triangle_centers = np.array(triangle_centers)

# Calculate potential with 2-mile exclusion
tract_lons = df['LONGITUDE'].values
tract_lats = df['LATITUDE'].values
tract_pops = df['POPULATION'].values
avg_lat = np.mean(tract_lats)
cos_avg_lat = np.cos(np.radians(avg_lat))

potentials = np.zeros(len(triangle_centers))
chunk_size = 1000

for chunk_idx in range(0, len(triangle_centers), chunk_size):
    end_idx = min(chunk_idx + chunk_size, len(triangle_centers))
    centers_chunk = triangle_centers[chunk_idx:end_idx]

    dlon = (centers_chunk[:, 0, np.newaxis] - tract_lons) * cos_avg_lat
    dlat = centers_chunk[:, 1, np.newaxis] - tract_lats
    distances = np.sqrt(dlon**2 + dlat**2) * 69.0

    valid_mask = distances > 2.0
    contributions = np.where(valid_mask, tract_pops / (distances ** 3), 0.0)
    potentials[chunk_idx:end_idx] = np.sum(contributions, axis=1)

print(f"Potential range: {potentials.min():.2e} to {potentials.max():.2e}")

# Save
output_path = Path(f"output/{region_name}/triangle_centers_d3_potential_2mile.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_data = np.column_stack((triangle_centers[:, 0], triangle_centers[:, 1], potentials))
np.savetxt(output_path, output_data, delimiter=',', fmt='%.6f,%.6f,%.8e')
print(f"Saved to {output_path}")
EOFPYTHON

python3 /tmp/calc_${REGION}.py "$REGION" "$INPUT_CSV"

# Generate mesh viz
python3 - "$REGION" << 'EOFVIZ'
import sys
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Delaunay
from pathlib import Path

region = sys.argv[1]
data = np.loadtxt(f'output/{region}/triangle_centers_d3_potential_2mile.csv', delimiter=',')
lons, lats, potentials = data[:, 0], data[:, 1], data[:, 2]

tri = Delaunay(np.column_stack((lons, lats)))
lon_range = lons.max() - lons.min()
z_scaled = (potentials - potentials.min()) / (potentials.max() - potentials.min()) * (lon_range * 0.08)

fig = go.Figure(data=[go.Mesh3d(
    x=lons, y=lats, z=z_scaled,
    i=tri.simplices[:, 0], j=tri.simplices[:, 1], k=tri.simplices[:, 2],
    intensity=z_scaled, colorscale='Greys', showscale=True,
    colorbar=dict(title="Height"),
    hovertemplate='Lon: %{x:.2f}°<br>Lat: %{y:.2f}°<br>Height: %{z:.3f}°<extra></extra>',
    lighting=dict(ambient=0.5, diffuse=0.8, specular=0.2), flatshading=False
)])

fig.update_layout(
    title=f"{region.title()} - Triangle Mesh (2-Mile Exclusion)<br><sub>1/d³ potential | 8% Z aspect</sub>",
    scene=dict(
        xaxis=dict(title='Longitude (°)', showgrid=True, dtick=2),
        yaxis=dict(title='Latitude (°)', showgrid=True, dtick=1),
        zaxis=dict(title='Potential (scaled)', showgrid=True),
        aspectmode='data',
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
        bgcolor='white'
    ),
    width=1600, height=1000
)

fig.write_html(f'output/{region}/preview_mesh_2mile.html')
print(f"Saved mesh to output/{region}/preview_mesh_2mile.html")

# Generate surface viz
from scipy.interpolate import griddata
grid_lon = np.linspace(lons.min(), lons.max(), 300)
grid_lat = np.linspace(lats.min(), lats.max(), 200)
lon_mesh, lat_mesh = np.meshgrid(grid_lon, grid_lat)
pot_mesh = griddata(np.column_stack((lons, lats)), potentials, (lon_mesh, lat_mesh), method='linear')
pot_mesh = np.nan_to_num(pot_mesh, nan=potentials.min())
z_mesh = (pot_mesh - potentials.min()) / (potentials.max() - potentials.min()) * (lon_range * 0.08)

fig2 = go.Figure(data=[go.Surface(
    x=lon_mesh, y=lat_mesh, z=z_mesh,
    colorscale='Greys', showscale=True,
    colorbar=dict(title="Height"),
    lighting=dict(ambient=0.5, diffuse=0.8, specular=0.2)
)])

fig2.update_layout(
    title=f"{region.title()} - Interpolated Surface (2-Mile Exclusion)<br><sub>1/d³ potential | 8% Z aspect</sub>",
    scene=dict(
        xaxis=dict(title='Longitude (°)', showgrid=True, dtick=2),
        yaxis=dict(title='Latitude (°)', showgrid=True, dtick=1),
        zaxis=dict(title='Potential (scaled)', showgrid=True),
        aspectmode='data',
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
        bgcolor='white'
    ),
    width=1600, height=1000
)

fig2.write_html(f'output/{region}/preview_surface_2mile.html')
print(f"Saved surface to output/{region}/preview_surface_2mile.html")
EOFVIZ

echo "Done! Open:"
echo "  output/$REGION/preview_mesh_2mile.html"
echo "  output/$REGION/preview_surface_2mile.html"
