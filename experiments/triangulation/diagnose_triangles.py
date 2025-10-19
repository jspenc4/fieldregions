#!/usr/bin/env python3
"""
Diagnose triangle mesh quality and potential calculation issues.
"""

import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from scipy.spatial.distance import cdist

print("="*70)
print("TRIANGLE MESH DIAGNOSTIC")
print("="*70)

# Load census tracts
print("\nLoading census tract data...")
census_df = pd.read_csv('res/censusTracts.csv')
census_points = np.column_stack((census_df['LONGITUDE'].values, census_df['LATITUDE'].values))
print(f"Loaded {len(census_points):,} census tracts")

# Load triangle centers with potential
print("Loading triangle center data...")
triangle_data = np.loadtxt('output/usa/triangle_centers_d3_potential.csv', delimiter=',')
triangle_centers = triangle_data[:, 0:2]  # lon, lat
potentials = triangle_data[:, 2]
print(f"Loaded {len(triangle_centers):,} triangle centers")

# Triangulate census points to analyze geometry
print("\nTriangulating census points...")
tri = Delaunay(census_points)
print(f"Created {len(tri.simplices):,} triangles")

# Analyze triangle geometry
print("\n" + "="*70)
print("TRIANGLE GEOMETRY ANALYSIS")
print("="*70)

areas = []
aspect_ratios = []

for i, triangle_idx in enumerate(tri.simplices[:10000]):  # Sample first 10k
    p0 = census_points[triangle_idx[0]]
    p1 = census_points[triangle_idx[1]]
    p2 = census_points[triangle_idx[2]]

    # Calculate area using cross product
    v1 = p1 - p0
    v2 = p2 - p0
    area = 0.5 * abs(np.cross(v1, v2))
    areas.append(area)

    # Calculate aspect ratio (longest edge / shortest edge)
    edge1 = np.linalg.norm(p1 - p0)
    edge2 = np.linalg.norm(p2 - p1)
    edge3 = np.linalg.norm(p0 - p2)
    edges = [edge1, edge2, edge3]
    aspect = max(edges) / min(edges)
    aspect_ratios.append(aspect)

areas = np.array(areas)
aspect_ratios = np.array(aspect_ratios)

print(f"\nTriangle areas (degrees²):")
print(f"  Min:    {areas.min():.6f}")
print(f"  Median: {np.median(areas):.6f}")
print(f"  Max:    {areas.max():.6f}")
print(f"  Mean:   {areas.mean():.6f}")

print(f"\nAspect ratios (max_edge / min_edge):")
print(f"  Min:    {aspect_ratios.min():.2f}")
print(f"  Median: {np.median(aspect_ratios):.2f}")
print(f"  90th %: {np.percentile(aspect_ratios, 90):.2f}")
print(f"  95th %: {np.percentile(aspect_ratios, 95):.2f}")
print(f"  99th %: {np.percentile(aspect_ratios, 99):.2f}")
print(f"  Max:    {aspect_ratios.max():.2f}")

bad_triangles = np.sum(aspect_ratios > 10)
print(f"\nTriangles with aspect ratio > 10: {bad_triangles:,} ({bad_triangles/len(aspect_ratios)*100:.1f}%)")

# Analyze distances between triangle centers and census tracts
print("\n" + "="*70)
print("TRIANGLE CENTER TO CENSUS TRACT DISTANCES")
print("="*70)

print("\nCalculating nearest census tract for each triangle center...")
print("(This may take a minute...)")

# Calculate distances from each triangle center to all census points
# Do in chunks to avoid memory issues
chunk_size = 1000
min_distances = []

for i in range(0, len(triangle_centers), chunk_size):
    end = min(i + chunk_size, len(triangle_centers))
    chunk = triangle_centers[i:end]

    # Calculate distances to all census points
    distances = cdist(chunk, census_points)

    # Find minimum distance for each triangle center
    chunk_min_dist = distances.min(axis=1)
    min_distances.extend(chunk_min_dist)

    if i % 10000 == 0:
        print(f"  Processed {i:,}/{len(triangle_centers):,} centers...")

min_distances = np.array(min_distances)

# Convert to miles (rough approximation: 1 degree ≈ 69 miles at US latitudes)
min_distances_miles = min_distances * 69

print(f"\nMinimum distance from triangle center to nearest census tract:")
print(f"  Min:     {min_distances_miles.min():.6f} miles ({min_distances_miles.min()*5280:.1f} feet)")
print(f"  1st %:   {np.percentile(min_distances_miles, 1):.6f} miles")
print(f"  5th %:   {np.percentile(min_distances_miles, 5):.6f} miles")
print(f"  Median:  {np.median(min_distances_miles):.6f} miles")
print(f"  95th %:  {np.percentile(min_distances_miles, 95):.6f} miles")
print(f"  Max:     {min_distances_miles.max():.6f} miles")

very_close = np.sum(min_distances_miles < 0.01)
print(f"\nTriangle centers within 0.01 miles (53 feet): {very_close:,} ({very_close/len(min_distances)*100:.1f}%)")

extremely_close = np.sum(min_distances_miles < 0.001)
print(f"Triangle centers within 0.001 miles (5 feet): {extremely_close:,} ({extremely_close/len(min_distances)*100:.1f}%)")

# Analyze potential distribution
print("\n" + "="*70)
print("POTENTIAL DISTRIBUTION ANALYSIS")
print("="*70)

print(f"\nOverall potential statistics:")
print(f"  Min:     {potentials.min():.2e}")
print(f"  1st %:   {np.percentile(potentials, 1):.2e}")
print(f"  Median:  {np.median(potentials):.2e}")
print(f"  99th %:  {np.percentile(potentials, 99):.2e}")
print(f"  Max:     {potentials.max():.2e}")

# Look at NYC area (rough bounds)
nyc_mask = (triangle_centers[:, 0] > -74.5) & (triangle_centers[:, 0] < -73.5) & \
           (triangle_centers[:, 1] > 40.5) & (triangle_centers[:, 1] < 41.0)
nyc_potentials = potentials[nyc_mask]

print(f"\nNYC area potentials ({np.sum(nyc_mask):,} points):")
print(f"  Min:     {nyc_potentials.min():.2e}")
print(f"  1st %:   {np.percentile(nyc_potentials, 1):.2e}")
print(f"  Median:  {np.median(nyc_potentials):.2e}")
print(f"  99th %:  {np.percentile(nyc_potentials, 99):.2e}")
print(f"  Max:     {nyc_potentials.max():.2e}")

low_in_nyc = np.sum(nyc_potentials < 1000)
print(f"  Points with potential < 1000: {low_in_nyc} ({low_in_nyc/len(nyc_potentials)*100:.1f}%)")

# LA area
la_mask = (triangle_centers[:, 0] > -118.5) & (triangle_centers[:, 0] < -117.5) & \
          (triangle_centers[:, 1] > 33.5) & (triangle_centers[:, 1] < 34.5)
la_potentials = potentials[la_mask]

print(f"\nLA area potentials ({np.sum(la_mask):,} points):")
print(f"  Min:     {la_potentials.min():.2e}")
print(f"  1st %:   {np.percentile(la_potentials, 1):.2e}")
print(f"  Median:  {np.median(la_potentials):.2e}")
print(f"  99th %:  {np.percentile(la_potentials, 99):.2e}")
print(f"  Max:     {la_potentials.max():.2e}")

low_in_la = np.sum(la_potentials < 1000)
print(f"  Points with potential < 1000: {low_in_la} ({low_in_la/len(la_potentials)*100:.1f}%)")

print("\n" + "="*70)
print("DIAGNOSIS COMPLETE")
print("="*70)
