#!/usr/bin/env python3
"""
Calculate topographic prominence for gridded population potential data.

Uses watershed algorithm on regular 2D grid.
"""

import argparse
import csv
import sys
import numpy as np
from scipy import ndimage
from scipy.ndimage import label


def load_gridded_data(filename):
    """Load CSV and convert to 2D grid."""
    print(f"Loading {filename}...")

    lons, lats, pops, pots = [], [], [], []
    with open(filename) as f:
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

    # Determine grid dimensions
    unique_lons = np.unique(lons)
    unique_lats = np.unique(lats)

    print(f"  Grid: {len(unique_lats)} latitudes × {len(unique_lons)} longitudes")
    print(f"  Lat range: [{unique_lats.min():.2f}, {unique_lats.max():.2f}]")
    print(f"  Lon range: [{unique_lons.min():.2f}, {unique_lons.max():.2f}]")

    # Create mapping from (lat, lon) to grid indices
    lat_to_idx = {lat: i for i, lat in enumerate(sorted(unique_lats, reverse=True))}  # Top to bottom
    lon_to_idx = {lon: i for i, lon in enumerate(sorted(unique_lons))}  # Left to right

    # Build 2D arrays
    grid_shape = (len(unique_lats), len(unique_lons))
    pot_grid = np.full(grid_shape, np.nan)
    pop_grid = np.full(grid_shape, 0)

    for lon, lat, pop, pot in zip(lons, lats, pops, pots):
        i = lat_to_idx[lat]
        j = lon_to_idx[lon]
        pot_grid[i, j] = pot
        pop_grid[i, j] = pop

    return pot_grid, pop_grid, unique_lats, unique_lons


def find_peaks_and_prominences(pot_grid, pop_grid, min_prominence=100):
    """Find peaks and calculate prominence using watershed."""
    print(f"\nFinding peaks and calculating prominence...")

    # Replace NaN with -inf for processing
    data = np.copy(pot_grid)
    data[np.isnan(data)] = -np.inf

    # Find local maxima
    print("  Finding local maxima...")
    # A point is a local max if it's >= all 8 neighbors
    local_max = ndimage.maximum_filter(data, size=3) == data
    # Exclude points at -inf
    local_max[data == -inf] = False

    peak_indices = np.argwhere(local_max)
    n_peaks = len(peak_indices)
    print(f"  Found {n_peaks:,} local maxima")

    # Calculate prominence using inverse watershed
    # Key insight: prominence is the depth you must descend to reach higher ground
    # This is equivalent to: pot[peak] - max(key_cols to all higher peaks)

    print("  Calculating prominences...")
    peak_pots = data[local_max]
    sorted_peak_indices = np.argsort(-peak_pots)  # Sort by height, tallest first

    prominences = np.zeros(n_peaks)

    # Tallest peak has prominence = its height
    prominences[sorted_peak_indices[0]] = peak_pots[sorted_peak_indices[0]]
    print(f"  Peak 1/{n_peaks}: prominence = {prominences[sorted_peak_indices[0]]:.1f} (global max)")

    # For each remaining peak, find its prominence
    for rank, peak_idx in enumerate(sorted_peak_indices[1:], start=2):
        if rank % 100 == 0:
            print(f"  Processing peak {rank:,}/{n_peaks:,}...")

        peak_i, peak_j = peak_indices[peak_idx]
        peak_pot = data[peak_i, peak_j]

        # Find the key col by checking saddles to all higher peaks
        # Use flood-fill approach: expand from peak until hitting higher ground
        # Track the maximum "low point" encountered (the saddle)

        visited = np.zeros_like(data, dtype=bool)
        queue = [(peak_i, peak_j)]
        visited[peak_i, peak_j] = True
        key_col = -np.inf

        while queue:
            i, j = queue.pop(0)
            current_pot = data[i, j]

            # Check 8 neighbors
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if di == 0 and dj == 0:
                        continue

                    ni, nj = i + di, j + dj

                    # Check bounds
                    if not (0 <= ni < data.shape[0] and 0 <= nj < data.shape[1]):
                        continue

                    if visited[ni, nj]:
                        continue

                    neighbor_pot = data[ni, nj]

                    # If we hit higher ground, this path gives us a saddle
                    if neighbor_pot > peak_pot:
                        key_col = max(key_col, current_pot)
                        continue

                    # Otherwise, continue expanding
                    visited[ni, nj] = True
                    queue.append((ni, nj))

        prominence = peak_pot - key_col
        prominences[peak_idx] = prominence

    return peak_indices, prominences, data


def main():
    parser = argparse.ArgumentParser(description='Calculate prominence for gridded data')
    parser.add_argument('potential_file', help='CSV with LONGITUDE,LATITUDE,POPULATION,POTENTIAL')
    parser.add_argument('--min-prominence', type=float, default=100,
                       help='Minimum prominence to include (default: 100)')
    parser.add_argument('--top', type=int, default=100,
                       help='Number of top peaks to output (default: 100)')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')

    args = parser.parse_args()

    # Load gridded data
    pot_grid, pop_grid, lats, lons = load_gridded_data(args.potential_file)

    # Find peaks and prominences
    peak_indices, prominences, pot_data = find_peaks_and_prominences(pot_grid, pop_grid, args.min_prominence)

    # Filter and sort results
    print(f"\nFiltering peaks...")
    results = []
    for idx, (i, j) in enumerate(peak_indices):
        if prominences[idx] >= args.min_prominence:
            results.append({
                'prominence': prominences[idx],
                'potential': pot_data[i, j],
                'latitude': lats[i],
                'longitude': lons[j],
                'population': int(pop_grid[i, j])
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
