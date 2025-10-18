#!/usr/bin/env python3
"""
Step 2 (Modified): Calculate 1/d³ potential at triangle centers, EXCLUDING triangle vertices.

Key change: Each triangle center's potential excludes the 3 census tracts that form
its triangle vertices. This treats census tract points as area labels (not point masses)
and prevents artificial spikes from nearest neighbors.

Input:  output/usa/triangle_centers_geom.csv (~145k triangle centers: lon, lat)
        res/censusTracts.csv (72k census tracts: lon, lat, pop)
Output: output/usa/triangle_centers_d3_potential_exclude.csv (~145k: lon, lat, potential)

Performance: ~72 seconds for USA
"""

import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path
from datetime import datetime
import sys

def log(msg):
    """Print timestamped log message."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def main():
    print("="*70)
    print("USA 1/d³ POTENTIAL CALCULATION (EXCLUDING TRIANGLE VERTICES)")
    print("="*70)
    print()

    # Load census tracts FIRST (need for triangulation)
    log("Loading census tract data...")
    census_path = Path("res/censusTracts.csv")

    if not census_path.exists():
        print(f"ERROR: Census data not found: {census_path}")
        return 1

    df = pd.read_csv(census_path)
    log(f"Loaded {len(df):,} census tracts")

    # Create Delaunay triangulation to get vertex mappings
    log("Computing Delaunay triangulation to identify triangle vertices...")
    census_points = np.column_stack((df['LONGITUDE'].values, df['LATITUDE'].values))
    tri = Delaunay(census_points)
    log(f"Created {len(tri.simplices):,} triangles")

    # Calculate triangle centers (must match 01_triangulate_usa.py)
    log("Calculating triangle centers...")
    triangle_centers = []
    triangle_vertex_indices = []  # Track which census tracts form each triangle

    for i, triangle_idx in enumerate(tri.simplices):
        if i % 50000 == 0 and i > 0:
            log(f"  Processed {i:,}/{len(tri.simplices):,} triangles...")

        p0 = census_points[triangle_idx[0]]
        p1 = census_points[triangle_idx[1]]
        p2 = census_points[triangle_idx[2]]
        center = (p0 + p1 + p2) / 3.0

        triangle_centers.append(center)
        triangle_vertex_indices.append(triangle_idx)  # Store the 3 vertex indices

    triangle_centers = np.array(triangle_centers)
    triangle_vertex_indices = np.array(triangle_vertex_indices)
    log(f"Calculated {len(triangle_centers):,} triangle centers")

    # Extract census tract data
    tract_lons = df['LONGITUDE'].values
    tract_lats = df['LATITUDE'].values
    tract_pops = df['POPULATION'].values

    # Calculate average latitude for longitude scaling
    avg_lat = np.mean(tract_lats)
    cos_avg_lat = np.cos(np.radians(avg_lat))

    log(f"Average latitude: {avg_lat:.2f}° (cos = {cos_avg_lat:.4f})")

    # Calculate potential at each triangle center (EXCLUDING its vertices)
    log("")
    log("Calculating 1/d³ potential at triangle centers...")
    log("EXCLUDING the 3 census tracts that form each triangle's vertices")
    log("Using vectorized algorithm with chunked processing")
    log("")

    potentials_at_centers = np.zeros(len(triangle_centers))

    chunk_size = 1000
    num_chunks = (len(triangle_centers) + chunk_size - 1) // chunk_size

    for chunk_idx in range(num_chunks):
        start_idx = chunk_idx * chunk_size
        end_idx = min(start_idx + chunk_size, len(triangle_centers))

        # Progress logging
        if chunk_idx % 10 == 0 or chunk_idx == num_chunks - 1:
            pct = 100 * start_idx / len(triangle_centers)
            log(f"  Processing centers {start_idx:,}/{len(triangle_centers):,} ({pct:.1f}%)")

        # Get chunk of centers and their vertex indices
        centers_chunk = triangle_centers[start_idx:end_idx]
        vertices_chunk = triangle_vertex_indices[start_idx:end_idx]

        center_lons = centers_chunk[:, 0]  # shape: (chunk_size,)
        center_lats = centers_chunk[:, 1]  # shape: (chunk_size,)

        # Vectorized distance calculation
        # Broadcast to get all pairwise distances: (chunk_size, num_tracts)
        dlon = (center_lons[:, np.newaxis] - tract_lons[np.newaxis, :]) * cos_avg_lat
        dlat = center_lats[:, np.newaxis] - tract_lats[np.newaxis, :]

        # Euclidean distance in scaled (lon, lat) space
        # Multiply by ~69 miles/degree
        distances = np.sqrt(dlon**2 + dlat**2) * 69.0

        # Clamp minimum distance to avoid numerical issues
        distances = np.maximum(distances, 0.001)

        # Calculate contributions: population / distance³
        contributions = tract_pops[np.newaxis, :] / (distances ** 3)

        # NEW: Zero out contributions from triangle vertices
        # For each triangle center i in chunk, set contributions from its 3 vertices to 0
        for i in range(len(centers_chunk)):
            v0, v1, v2 = vertices_chunk[i]
            contributions[i, v0] = 0.0
            contributions[i, v1] = 0.0
            contributions[i, v2] = 0.0

        # Sum contributions for each center in chunk
        potentials_chunk = np.sum(contributions, axis=1)
        potentials_at_centers[start_idx:end_idx] = potentials_chunk

    log("")
    log(f"Potential range: {potentials_at_centers.min():.2e} to {potentials_at_centers.max():.2e}")

    # Save results
    output_path = Path("output/usa/triangle_centers_d3_potential_exclude.csv")
    log(f"Saving to {output_path}...")

    # Combine lon, lat, potential
    output_data = np.column_stack((
        triangle_centers[:, 0],  # lon
        triangle_centers[:, 1],  # lat
        potentials_at_centers    # potential
    ))

    # Save as lon,lat,potential (no header)
    np.savetxt(output_path, output_data, delimiter=',', fmt='%.6f,%.6f,%.8e')

    log(f"✓ Saved {len(output_data):,} points with potential values")

    print()
    print("="*70)
    print("POTENTIAL CALCULATION COMPLETE (VERTICES EXCLUDED)")
    print("="*70)
    print(f"Input:     {len(triangle_centers):,} triangle centers")
    print(f"           {len(df):,} census tracts")
    print(f"Output:    {len(output_data):,} points with potential")
    print(f"File:      {output_path}")
    print(f"Potential: {potentials_at_centers.min():.2e} to {potentials_at_centers.max():.2e}")
    print(f"Method:    Each triangle excludes its 3 vertices from calculation")
    print("="*70)

    return 0

if __name__ == "__main__":
    exit(main())
