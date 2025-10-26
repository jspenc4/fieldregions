#!/usr/bin/env python3
"""
Calculate topographic prominence for population potential peaks.

Based on the standard algorithm:
1. Find all local maxima (peaks)
2. For each peak, find its "key col" - the lowest point you must descend
   to before reaching higher ground
3. Prominence = peak height - key col height

Uses scipy's island prominence algorithm adapted for 2D geographic data.
"""

import argparse
import csv
import sys
import numpy as np
from scipy.spatial import cKDTree
from collections import deque


def haversine_distance_vec(lat1, lon1, lat2_arr, lon2_arr):
    """Vectorized haversine distance in miles."""
    R = 3959  # Earth radius in miles
    lat1, lon1 = np.radians(lat1), np.radians(lon1)
    lat2_arr = np.radians(lat2_arr)
    lon2_arr = np.radians(lon2_arr)

    dlat = lat2_arr - lat1
    dlon = lon2_arr - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2_arr) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    return R * c


def find_local_maxima(lats, lons, potentials, radius_miles):
    """Find local maxima - points higher than all neighbors within radius."""
    print(f"Finding local maxima...")
    print(f"  Checking for local maxima...")

    # Build KD-tree (using lat/lon in degrees as approximation)
    coords = np.column_stack([lats, lons])
    tree = cKDTree(coords)

    # Convert radius to degrees (approximate)
    radius_deg = radius_miles / 69.0  # ~69 miles per degree latitude

    maxima_indices = []

    for i in range(len(potentials)):
        if i % 10000 == 0:
            print(f"    Processed {i:,}/{len(potentials):,}...")

        # Find neighbors
        neighbor_indices = tree.query_ball_point([lats[i], lons[i]], radius_deg)

        # Is this point >= all neighbors?
        is_max = all(potentials[i] >= potentials[j] for j in neighbor_indices)

        if is_max:
            maxima_indices.append(i)

    print(f"  Found {len(maxima_indices):,} local maxima")
    return np.array(maxima_indices)


def calculate_prominences(lats, lons, potentials, peak_indices, tree):
    """
    Calculate prominence using watershed algorithm.

    For each peak:
    1. Start at the peak
    2. Expand outward keeping track of minimum encountered
    3. Stop when we hit a higher peak or edge of domain
    4. Prominence = peak - min_encountered
    """
    print(f"\nCalculating prominences...")

    n_peaks = len(peak_indices)
    prominences = np.zeros(n_peaks)

    # Sort peaks by height (tallest first)
    sorted_indices = np.argsort(-potentials[peak_indices])

    # Track which peak "owns" each point (watershed basins)
    basin = np.full(len(potentials), -1, dtype=int)

    # Tallest peak has prominence = its height (reference level = 0)
    tallest_idx = sorted_indices[0]
    peak_position = peak_indices[tallest_idx]
    prominences[tallest_idx] = potentials[peak_position]
    basin[peak_position] = tallest_idx

    print(f"  Peak 1/{n_peaks}: prominence = {prominences[tallest_idx]:.1f} (global max)")

    # Process remaining peaks in descending order
    for peak_rank, peak_idx in enumerate(sorted_indices[1:], start=2):
        if peak_rank % 100 == 0:
            print(f"  Processing peak {peak_rank:,}/{n_peaks:,}...")

        peak_position = peak_indices[peak_idx]
        peak_height = potentials[peak_position]

        # BFS/flood fill from peak until we hit higher ground
        visited = set([peak_position])
        queue = deque([peak_position])
        key_col = peak_height  # Start assuming we don't descend

        while queue:
            current = queue.popleft()
            current_height = potentials[current]

            # Update key col (lowest point encountered)
            key_col = min(key_col, current_height)

            # Find neighbors (within ~20 miles for efficiency)
            neighbor_indices = tree.query_ball_point(
                [lats[current], lons[current]],
                20.0 / 69.0  # 20 miles in degrees
            )

            for neighbor in neighbor_indices:
                if neighbor in visited:
                    continue

                neighbor_height = potentials[neighbor]

                # Stop if we hit higher ground
                if neighbor_height > peak_height:
                    break

                # Continue flooding if lower
                visited.add(neighbor)
                queue.append(neighbor)

        prominence = peak_height - key_col
        prominences[peak_idx] = prominence

        # Mark basin
        for point in visited:
            if basin[point] == -1:
                basin[point] = peak_idx

    return prominences


def main():
    parser = argparse.ArgumentParser(description='Calculate peak prominences')
    parser.add_argument('potential_file', help='CSV with LONGITUDE,LATITUDE,POPULATION,POTENTIAL')
    parser.add_argument('--radius', type=float, default=50,
                       help='Radius for local maxima detection (miles, default: 50)')
    parser.add_argument('--min-prominence', type=float, default=100,
                       help='Minimum prominence to include (default: 100)')
    parser.add_argument('--top', type=int, default=100,
                       help='Number of top peaks to output (default: 100)')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')

    args = parser.parse_args()

    # Load data
    print(f"Loading {args.potential_file}...")
    lons, lats, pops, pots = [], [], [], []

    with open(args.potential_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            lons.append(float(row['LONGITUDE']))
            lats.append(float(row['LATITUDE']))
            pops.append(int(row['POPULATION']))
            pots.append(float(row['POTENTIAL']))

    lons = np.array(lons)
    lats = np.array(lats)
    pops = np.array(pops)
    pots = np.array(pots)

    print(f"  Loaded {len(pots):,} points")
    print(f"  Potential range: [{pots.min():.1f}, {pots.max():.1f}]")

    # Build spatial index
    coords = np.column_stack([lats, lons])
    tree = cKDTree(coords)

    # Find peaks
    peak_indices = find_local_maxima(lats, lons, pots, args.radius)

    # Calculate prominences
    prominences = calculate_prominences(lats, lons, pots, peak_indices, tree)

    # Filter and sort
    print(f"\nFiltering peaks...")
    results = []
    for i, peak_idx in enumerate(peak_indices):
        if prominences[i] >= args.min_prominence:
            results.append({
                'prominence': prominences[i],
                'potential': pots[peak_idx],
                'latitude': lats[peak_idx],
                'longitude': lons[peak_idx],
                'population': pops[peak_idx]
            })

    results.sort(key=lambda x: x['prominence'], reverse=True)
    results = results[:args.top]

    print(f"  {len(results)} peaks above prominence threshold")

    # Output
    out = open(args.output, 'w') if args.output else sys.stdout

    print(f"\nTop {len(results)} peaks by prominence:", file=out)
    print("="*100, file=out)
    print(f"{'Rank':<6} {'Prominence':<12} {'Peak Height':<12} {'Latitude':<12} {'Longitude':<12} {'Population':<12}", file=out)
    print("-"*100, file=out)

    for rank, peak in enumerate(results, 1):
        print(f"{rank:<6} {peak['prominence']:<12,.0f} {peak['potential']:<12,.0f} "
              f"{peak['latitude']:<12.4f} {peak['longitude']:<12.4f} {peak['population']:<12,}",
              file=out)

    if args.output:
        out.close()
        print(f"\nSaving to {args.output}...")
        print(f"Done!")


if __name__ == '__main__':
    main()
