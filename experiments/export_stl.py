#!/usr/bin/env python3
"""
Export population potential surface as STL file for 3D printing.
Uses linear Z scaling for printability.
"""

import numpy as np
from scipy.spatial import Delaunay
from stl import mesh

# Load USA natural data
print("Loading USA natural potential data...")
data = np.loadtxt('output/usa_natural/census_tract_potential.csv', delimiter=',', skiprows=1)
lons = data[:, 0]
lats = data[:, 1]
potentials = data[:, 2]

print(f"Loaded {len(lons):,} points")
print(f"Lon range: {lons.min():.2f} to {lons.max():.2f}")
print(f"Lat range: {lats.min():.2f} to {lats.max():.2f}")
print(f"Potential range: {potentials.min():.2e} to {potentials.max():.2e}")

# Build triangulation
print("Building Delaunay triangulation...")
tri = Delaunay(np.column_stack((lons, lats)))
print(f"Triangles: {len(tri.simplices):,}")

# Normalize coordinates to fit on build plate
# Bambu P1S build volume: 256mm x 256mm x 256mm
# Use 200mm x 200mm to be safe
lon_range = lons.max() - lons.min()
lat_range = lats.max() - lats.min()
aspect = lat_range / lon_range

print(f"\nGeographic aspect ratio: {aspect:.3f}")

# Scale to fit 200mm width
scale_mm = 200.0 / lon_range
x_mm = (lons - lons.min()) * scale_mm
y_mm = (lats - lats.min()) * scale_mm

print(f"X range: 0 to {x_mm.max():.1f} mm")
print(f"Y range: 0 to {y_mm.max():.1f} mm")

# Z scaling: linear with configurable aspect ratio
# Use 9% for printable "gravitational" feel (similar to gravity visualization)
z_aspect = 0.09
p_shifted = potentials - potentials.min()
z_normalized = p_shifted / p_shifted.max()
z_mm = z_normalized * (200.0 * z_aspect)

# Add 2mm base plate
base_thickness = 2.0
z_mm += base_thickness

print(f"Z range: {z_mm.min():.1f} to {z_mm.max():.1f} mm")
print(f"Max height: {z_mm.max():.1f} mm (fits in 256mm build height)")

# Create mesh
print("\nCreating STL mesh...")
vertices = np.column_stack((x_mm, y_mm, z_mm))

# Create faces from triangulation
faces = tri.simplices

# Create mesh object
print(f"Creating mesh with {len(faces):,} triangles...")
surface_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))

for i, face in enumerate(faces):
    for j in range(3):
        surface_mesh.vectors[i][j] = vertices[face[j]]

    if i % 50000 == 0 and i > 0:
        print(f"  Progress: {i:,} / {len(faces):,} ({100*i/len(faces):.1f}%)")

# Save STL
output_path = 'output/usa_natural/usa_surface_9pct.stl'
print(f"\nSaving to {output_path}...")
surface_mesh.save(output_path)

# Print statistics
print(f"\nSTL Statistics:")
print(f"  Triangles: {len(surface_mesh.vectors):,}")
print(f"  Vertices: ~{len(lons):,} unique points")
print(f"  Dimensions: {x_mm.max():.1f} × {y_mm.max():.1f} × {z_mm.max():.1f} mm")
print(f"  File size: {len(surface_mesh.data) * surface_mesh.data.itemsize / 1024 / 1024:.1f} MB")
print(f"\nReady for 3D printing on Bambu P1S!")
print(f"Estimated print time: 8-12 hours at 0.2mm layer height")
