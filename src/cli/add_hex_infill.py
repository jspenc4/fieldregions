#!/usr/bin/env python3
"""
Add Hex Grid Infill to Population Data

Creates a combined dataset with original population points plus zero-population
hex grid points in sparse areas. This provides smooth visualization sampling
while preserving calculation accuracy.

Strategy:
1. Load population source points (census tracts, block groups, etc.)
2. Generate hexagonal grid at specified spacing
3. Filter: keep only hex points >spacing from any source point
4. Set population=0 on hex points (they receive potential but don't contribute)
5. Combine source + hex points into single CSV

This allows potential calculation to sample smoothly in sparse coastal/desert
areas without adding artificial population mass.

Usage:
    python3 add_hex_infill.py <input_csv> <spacing_miles> [--buffer DEGREES] [--output FILE]

Examples:
    python3 add_hex_infill.py res/tracts_sf_bay.csv 5.0
    python3 add_hex_infill.py res/blockgroups_conus.csv 10.0 --buffer 1.0
    python3 add_hex_infill.py res/blockgroups_conus.csv 5.0 --output res/blockgroups_conus_hex5mi.csv
"""

import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib import io


def generate_hex_grid(lon_min, lon_max, lat_min, lat_max, spacing_miles=5.0, avg_lat=None):
    """
    Generate hexagonal grid of points.

    Hexagonal grids provide more uniform coverage than square grids.

    Parameters
    ----------
    lon_min, lon_max, lat_min, lat_max : float
        Bounding box for grid generation
    spacing_miles : float
        Distance between grid points in miles
    avg_lat : float, optional
        Average latitude for degree conversion (defaults to box center)

    Returns
    -------
    ndarray (N, 2)
        Array of [lon, lat] grid points
    """
    if avg_lat is None:
        avg_lat = (lat_min + lat_max) / 2

    cos_lat = np.cos(np.radians(avg_lat))

    # Convert spacing from miles to degrees
    # 1 degree latitude ≈ 69 miles
    spacing_deg_lat = spacing_miles / 69.0
    spacing_deg_lon = spacing_miles / (69.0 * cos_lat)

    # Create hexagonal grid with offset rows
    lats = np.arange(lat_min, lat_max, spacing_deg_lat)
    lons = np.arange(lon_min, lon_max, spacing_deg_lon)

    grid_points = []
    for i, lat in enumerate(lats):
        # Offset every other row by half spacing (hexagonal packing)
        lon_offset = spacing_deg_lon / 2 if i % 2 == 1 else 0
        for lon in lons:
            grid_points.append([lon + lon_offset, lat])

    return np.array(grid_points)


def filter_grid_by_distance(grid_points, source_points, min_distance_miles=5.0, avg_lat=None):
    """
    Keep only grid points that are >min_distance from any source point.

    This fills sparse areas without duplicating urban density.

    Parameters
    ----------
    grid_points : ndarray (M, 2)
        Candidate hex grid points [lon, lat]
    source_points : ndarray (N, 2)
        Population source points [lon, lat]
    min_distance_miles : float
        Minimum distance from sources to keep grid point
    avg_lat : float, optional
        Average latitude for distance calculation

    Returns
    -------
    ndarray (K, 2)
        Filtered grid points (K <= M)
    """
    if avg_lat is None:
        avg_lat = np.mean(source_points[:, 1])

    cos_lat = np.cos(np.radians(avg_lat))

    kept_points = []

    print(f"  Filtering {len(grid_points):,} candidate hex points...")

    # Vectorized distance calculation (more efficient than loop)
    for grid_pt in grid_points:
        # Calculate distance to all source points (cosine-corrected)
        dlon = (grid_pt[0] - source_points[:, 0]) * cos_lat
        dlat = grid_pt[1] - source_points[:, 1]
        distances_deg = np.sqrt(dlon**2 + dlat**2)
        distances_miles = distances_deg * 69.0

        min_dist = distances_miles.min()

        # Keep if far enough from all source points
        if min_dist > min_distance_miles:
            kept_points.append(grid_pt)

    kept_count = len(kept_points)
    filtered_count = len(grid_points) - kept_count
    print(f"  Kept {kept_count:,} hex points (filtered {filtered_count:,} too close to sources)")

    return np.array(kept_points) if kept_points else np.empty((0, 2))


def main():
    print("Hex Grid Infill Preprocessor v0.1")
    print("=" * 60)

    # Parse arguments
    if len(sys.argv) < 3:
        print("\nUsage: python3 add_hex_infill.py <input_csv> <spacing_miles> [--buffer DEGREES] [--output FILE]")
        print("\nExamples:")
        print("  python3 add_hex_infill.py res/tracts_sf_bay.csv 5.0")
        print("  python3 add_hex_infill.py res/blockgroups_conus.csv 10.0 --buffer 1.0")
        print("  python3 add_hex_infill.py res/blockgroups_conus.csv 5.0 --output res/blockgroups_conus_hex5mi.csv")
        sys.exit(1)

    # Parse --buffer flag
    buffer_deg = 0.5  # default
    buffer_value = None
    for i, arg in enumerate(sys.argv):
        if arg == '--buffer' and i + 1 < len(sys.argv):
            buffer_deg = float(sys.argv[i + 1])
            buffer_value = sys.argv[i + 1]

    # Parse --output flag
    output_file = None
    output_value = None
    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            output_value = sys.argv[i + 1]

    # Parse positional args
    flag_values = {buffer_value, output_value} - {None}
    args = [a for a in sys.argv[1:] if not a.startswith('--') and a not in flag_values]

    input_file = args[0]
    spacing_miles = float(args[1])

    # Default output filename
    if output_file is None:
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_hex{spacing_miles:.0f}mi{input_path.suffix}")

    # Load source data
    print(f"\nLoading source points from {input_file}...")
    df_sources = io.load_csv(input_file)
    source_points = np.column_stack((df_sources['LONGITUDE'].values, df_sources['LATITUDE'].values))
    print(f"  Loaded {len(source_points):,} source points")
    print(f"  Total population: {df_sources['POPULATION'].sum():,}")

    # Calculate bounds with buffer
    lon_min, lon_max = source_points[:, 0].min(), source_points[:, 0].max()
    lat_min, lat_max = source_points[:, 1].min(), source_points[:, 1].max()

    lon_min_buffered = lon_min - buffer_deg
    lon_max_buffered = lon_max + buffer_deg
    lat_min_buffered = lat_min - buffer_deg
    lat_max_buffered = lat_max + buffer_deg

    avg_lat = (lat_min + lat_max) / 2

    print(f"\nBounds:")
    print(f"  Longitude: [{lon_min:.2f}, {lon_max:.2f}]")
    print(f"  Latitude:  [{lat_min:.2f}, {lat_max:.2f}]")
    print(f"  Buffer: {buffer_deg}° (~{buffer_deg * 69:.1f} miles)")

    # Generate hex grid
    print(f"\nGenerating hex grid ({spacing_miles}-mile spacing)...")
    grid_points = generate_hex_grid(
        lon_min_buffered, lon_max_buffered,
        lat_min_buffered, lat_max_buffered,
        spacing_miles=spacing_miles,
        avg_lat=avg_lat
    )
    print(f"  Generated {len(grid_points):,} candidate hex points")

    # Filter grid points
    hex_points = filter_grid_by_distance(
        grid_points,
        source_points,
        min_distance_miles=spacing_miles,
        avg_lat=avg_lat
    )

    # Create combined dataset
    print(f"\nCombining sources + hex infill...")

    if len(hex_points) > 0:
        # Create hex points dataframe (population = 0)
        df_hex = pd.DataFrame({
            'LONGITUDE': hex_points[:, 0],
            'LATITUDE': hex_points[:, 1],
            'POPULATION': 0  # Zero population - test masses only
        })

        # Combine
        df_combined = pd.concat([df_sources, df_hex], ignore_index=True)

        print(f"  Source points:     {len(df_sources):,}")
        print(f"  Hex infill points: {len(df_hex):,}")
        print(f"  Total points:      {len(df_combined):,}")
    else:
        print(f"  No hex infill needed (all grid points too close to sources)")
        df_combined = df_sources

    # Save output
    print(f"\nSaving to {output_file}...")
    df_combined.to_csv(output_file, index=False)

    print(f"\n✓ Done!")
    print(f"\nNext step:")
    print(f"  python3 src/cli/calculate_potential.py {output_file} <min_distance> --jobs 4")


if __name__ == '__main__':
    main()
