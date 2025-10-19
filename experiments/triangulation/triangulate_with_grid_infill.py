#!/usr/bin/env python3
"""
Create Delaunay triangulation with regularized grid infill.

Strategy:
1. Load census tract points
2. Expand region bounds by buffer (to avoid edge artifacts)
3. Generate hexagonal grid at 2-mile spacing
4. Keep grid points only if >2 miles from any census tract (fills sparse areas)
5. Combine census + infill points
6. Triangulate
7. Calculate triangle centers for sampling
"""

import numpy as np
import pandas as pd
from scipy.spatial import Delaunay
from pathlib import Path
import sys

def generate_hex_grid(lon_min, lon_max, lat_min, lat_max, spacing_miles=2.0, avg_lat=None):
    """
    Generate hexagonal grid of points.

    Hexagonal grids are more uniform than square grids.
    """
    if avg_lat is None:
        avg_lat = (lat_min + lat_max) / 2

    cos_lat = np.cos(np.radians(avg_lat))

    # Convert spacing from miles to degrees
    # 1 degree latitude ≈ 69 miles
    spacing_deg_lat = spacing_miles / 69.0
    spacing_deg_lon = spacing_miles / (69.0 * cos_lat)

    # Hexagonal grid has rows offset by half spacing
    lats = np.arange(lat_min, lat_max, spacing_deg_lat)
    lons = np.arange(lon_min, lon_max, spacing_deg_lon)

    grid_points = []
    for i, lat in enumerate(lats):
        # Offset every other row by half spacing (hexagonal packing)
        lon_offset = spacing_deg_lon / 2 if i % 2 == 1 else 0
        for lon in lons:
            grid_points.append([lon + lon_offset, lat])

    return np.array(grid_points)

def filter_grid_by_distance(grid_points, census_points, min_distance_miles=2.0, avg_lat=None):
    """
    Keep only grid points that are >min_distance from any census point.

    This fills in sparse rural areas without duplicating urban density.
    """
    if avg_lat is None:
        avg_lat = np.mean(census_points[:, 1])

    cos_lat = np.cos(np.radians(avg_lat))

    kept_points = []

    print(f"Filtering {len(grid_points):,} grid points...")

    for grid_pt in grid_points:
        # Calculate distance to all census points
        dlon = (grid_pt[0] - census_points[:, 0]) * cos_lat
        dlat = grid_pt[1] - census_points[:, 1]
        distances = np.sqrt(dlon**2 + dlat**2) * 69.0  # Convert to miles

        min_dist = distances.min()

        # Keep if >2 miles from any census point
        if min_dist > min_distance_miles:
            kept_points.append(grid_pt)

    print(f"Kept {len(kept_points):,} grid points (filtered out {len(grid_points) - len(kept_points):,})")

    return np.array(kept_points) if kept_points else np.empty((0, 2))

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 triangulate_with_grid_infill.py <input_csv> <output_dir> [buffer_degrees] [grid_spacing_miles]")
        print("Example: python3 triangulate_with_grid_infill.py res/tracts_california.csv output/california_grid 0.5 2.0")
        print("         python3 triangulate_with_grid_infill.py res/censusTracts.csv output/usa_grid 1.0 5.0")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_dir = Path(sys.argv[2])
    buffer_deg = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    grid_spacing_miles = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load census data
    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    census_points = np.column_stack((df['LONGITUDE'].values, df['LATITUDE'].values))
    print(f"Loaded {len(census_points):,} census tract points")

    # Calculate bounds with buffer
    lon_min, lon_max = census_points[:, 0].min(), census_points[:, 0].max()
    lat_min, lat_max = census_points[:, 1].min(), census_points[:, 1].max()

    lon_min_buffered = lon_min - buffer_deg
    lon_max_buffered = lon_max + buffer_deg
    lat_min_buffered = lat_min - buffer_deg
    lat_max_buffered = lat_max + buffer_deg

    avg_lat = (lat_min + lat_max) / 2

    print(f"Original bounds: lon=[{lon_min:.2f}, {lon_max:.2f}], lat=[{lat_min:.2f}, {lat_max:.2f}]")
    print(f"Buffered bounds: lon=[{lon_min_buffered:.2f}, {lon_max_buffered:.2f}], lat=[{lat_min_buffered:.2f}, {lat_max_buffered:.2f}]")
    print(f"Buffer: {buffer_deg}° (~{buffer_deg * 69:.1f} miles)")

    # Generate hexagonal grid
    print(f"\nGenerating hexagonal grid ({grid_spacing_miles}-mile spacing)...")
    grid_points = generate_hex_grid(
        lon_min_buffered, lon_max_buffered,
        lat_min_buffered, lat_max_buffered,
        spacing_miles=grid_spacing_miles,
        avg_lat=avg_lat
    )
    print(f"Generated {len(grid_points):,} grid points")

    # Filter grid: keep only points >grid_spacing from census points
    infill_points = filter_grid_by_distance(grid_points, census_points, min_distance_miles=grid_spacing_miles, avg_lat=avg_lat)

    if len(infill_points) > 0:
        print(f"\nInfill points: {len(infill_points):,}")
        # Combine census + infill
        combined_points = np.vstack([census_points, infill_points])
    else:
        print("\nNo infill points needed (all grid points too close to census points)")
        combined_points = census_points

    print(f"Total points for triangulation: {len(combined_points):,}")

    # Triangulate
    print("\nTriangulating...")
    tri = Delaunay(combined_points)
    print(f"Created {len(tri.simplices):,} triangles")

    # Calculate triangle centers
    print("Calculating triangle centers...")
    triangle_centers = []
    for simplex in tri.simplices:
        p0, p1, p2 = combined_points[simplex]
        center = (p0 + p1 + p2) / 3.0
        triangle_centers.append(center)
    triangle_centers = np.array(triangle_centers)

    print(f"Calculated {len(triangle_centers):,} triangle centers")

    # Filter triangle centers: remove points too far from any census tract
    # These would have negligible potential anyway
    print("\nFiltering triangle centers by proximity to census tracts...")
    max_distance_miles = 50.0  # Discard if >50 miles from any tract
    cos_lat = np.cos(np.radians(avg_lat))

    kept_centers = []
    for center in triangle_centers:
        dlon = (center[0] - census_points[:, 0]) * cos_lat
        dlat = center[1] - census_points[:, 1]
        distances = np.sqrt(dlon**2 + dlat**2) * 69.0
        min_dist = distances.min()

        if min_dist <= max_distance_miles:
            kept_centers.append(center)

    original_count = len(triangle_centers)
    triangle_centers = np.array(kept_centers)
    filtered_count = original_count - len(triangle_centers)
    print(f"Kept {len(triangle_centers):,} triangle centers (filtered {filtered_count:,} remote points)")
    print(f"Max distance threshold: {max_distance_miles} miles")

    # Save outputs
    # 1. Combined points (for reference)
    combined_path = output_dir / 'combined_points.csv'
    np.savetxt(combined_path, combined_points, delimiter=',', fmt='%.6f',
               header='longitude,latitude', comments='')
    print(f"\nSaved combined points to {combined_path}")

    # 2. Triangle centers (for potential calculation)
    centers_path = output_dir / 'triangle_centers_geom.csv'
    np.savetxt(centers_path, triangle_centers, delimiter=',', fmt='%.6f',
               header='longitude,latitude', comments='')
    print(f"Saved triangle centers to {centers_path}")

    # 3. Metadata
    metadata = {
        'census_points': len(census_points),
        'infill_points': len(infill_points),
        'total_points': len(combined_points),
        'triangles': original_count,
        'triangle_centers': len(triangle_centers),
        'triangle_centers_filtered': filtered_count,
        'buffer_degrees': buffer_deg,
        'grid_spacing_miles': grid_spacing_miles,
        'min_infill_distance_miles': grid_spacing_miles,
        'max_sample_distance_miles': 50.0,
    }

    metadata_path = output_dir / 'metadata.txt'
    with open(metadata_path, 'w') as f:
        for key, value in metadata.items():
            f.write(f"{key}: {value}\n")
    print(f"Saved metadata to {metadata_path}")

    print("\nDone!")
    print(f"Next step: calculate potential using {centers_path}")

if __name__ == '__main__':
    main()
