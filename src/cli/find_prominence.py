#!/usr/bin/env python3
"""
Find prominent peaks in population potential field using topographic prominence algorithm.

Prominence measures how much a peak "stands out" from its surroundings by finding
the minimum descent needed to reach higher terrain (the key col).
"""

import argparse
import csv
import sys
from scipy.signal import find_peaks
import numpy as np
from scipy.spatial import cKDTree


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate great circle distance in miles."""
    R = 3959  # Earth radius in miles

    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    return R * c


def find_local_maxima(points, potentials, radius_miles=50):
    """Find local maxima - points higher than all neighbors within radius."""
    print(f"Finding local maxima (radius={radius_miles} miles)...")

    # Build KD-tree for neighbor search (using approximate degrees)
    # 1 degree latitude ≈ 69 miles, longitude varies but use as approximation
    lat_lon = np.column_stack([points[:, 0], points[:, 1]])
    tree = cKDTree(lat_lon)

    # Convert radius to approximate degrees (conservative)
    radius_deg = radius_miles / 60  # ~69 miles per degree

    maxima = []
    for i, (pt, pot) in enumerate(zip(points, potentials)):
        if i % 10000 == 0:
            print(f"  Checked {i:,}/{len(points):,} points...")

        # Find neighbors within radius
        neighbors = tree.query_ball_point([pt[0], pt[1]], radius_deg)

        # Check if this point is highest among neighbors
        is_maximum = all(pot >= potentials[j] for j in neighbors)

        if is_maximum:
            maxima.append(i)

    print(f"  Found {len(maxima):,} local maxima")
    return maxima


def calculate_prominence(points, potentials, peak_indices):
    """
    Calculate prominence for each peak.

    Prominence = peak height - key col height
    where key col = minimum potential on path to higher peak

    Uses simple approach: for each peak, find the minimum potential
    encountered when moving toward any higher peak.
    """
    print(f"Calculating prominence for {len(peak_indices):,} peaks...")

    prominences = []

    for i, peak_idx in enumerate(peak_indices):
        if i % 100 == 0:
            print(f"  Processing peak {i:,}/{len(peak_indices):,}...")

        peak_height = potentials[peak_idx]
        peak_lat, peak_lon = points[peak_idx]

        # Find higher peaks
        higher_peaks = [j for j in peak_indices if potentials[j] > peak_height]

        if not higher_peaks:
            # This is the global maximum - prominence = height
            prominences.append(peak_height)
            continue

        # For each higher peak, find min potential on direct path
        # (Simplified: check all points within corridor to higher peak)
        min_col = peak_height  # Start with peak height

        for higher_idx in higher_peaks:
            higher_lat, higher_lon = points[higher_idx]

            # Check all points to find those on path between peaks
            for pt_idx, (lat, lon) in enumerate(points):
                # Simple test: is point roughly between peak and higher peak?
                dist_to_peak = haversine_distance(peak_lat, peak_lon, lat, lon)
                dist_to_higher = haversine_distance(higher_lat, higher_lon, lat, lon)
                dist_peak_to_higher = haversine_distance(peak_lat, peak_lon, higher_lat, higher_lon)

                # Point is on path if distances roughly add up
                if abs((dist_to_peak + dist_to_higher) - dist_peak_to_higher) < 10:  # 10 mile tolerance
                    min_col = min(min_col, potentials[pt_idx])

        prominence = peak_height - min_col
        prominences.append(prominence)

    return prominences


def main():
    parser = argparse.ArgumentParser(description='Find prominent peaks in potential field')
    parser.add_argument('potential_file', help='CSV file with LONGITUDE,LATITUDE,POPULATION,POTENTIAL')
    parser.add_argument('--min-prominence', type=float, default=100,
                       help='Minimum prominence to include in output')
    parser.add_argument('--radius', type=float, default=50,
                       help='Radius in miles for local maxima detection (default: 50)')
    parser.add_argument('--top', type=int, default=100,
                       help='Number of top peaks to output (default: 100)')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')

    args = parser.parse_args()

    # Load potentials
    print(f"Loading {args.potential_file}...")
    lons, lats, pops, pots = [], [], [], []

    with open(args.potential_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            lons.append(float(row['LONGITUDE']))
            lats.append(float(row['LATITUDE']))
            pops.append(int(row['POPULATION']))
            pots.append(float(row['POTENTIAL']))

    points = np.column_stack([lats, lons])  # lat, lon order
    potentials = np.array(pots)

    print(f"  Loaded {len(points):,} points")
    print(f"  Potential range: [{potentials.min():.1f}, {potentials.max():.1f}]")

    # Find local maxima
    peak_indices = find_local_maxima(points, potentials, args.radius)

    # Calculate prominence
    prominences = calculate_prominence(points, potentials, peak_indices)

    # Sort by prominence
    peak_data = []
    for idx, prom in zip(peak_indices, prominences):
        if prom >= args.min_prominence:
            peak_data.append({
                'prominence': prom,
                'potential': potentials[idx],
                'latitude': lats[idx],
                'longitude': lons[idx],
                'population': pops[idx]
            })

    peak_data.sort(key=lambda x: x['prominence'], reverse=True)
    peak_data = peak_data[:args.top]

    # Output
    output = open(args.output, 'w') if args.output else sys.stdout

    print(f"\nTop {len(peak_data)} peaks by prominence:", file=output)
    print("="*100, file=output)
    print(f"{'Rank':<6} {'Prominence':<12} {'Potential':<12} {'Latitude':<12} {'Longitude':<12} {'Population':<12}", file=output)
    print("-"*100, file=output)

    for i, peak in enumerate(peak_data, 1):
        print(f"{i:<6} {peak['prominence']:<12.1f} {peak['potential']:<12.1f} "
              f"{peak['latitude']:<12.4f} {peak['longitude']:<12.4f} {peak['population']:<12,}",
              file=output)

    if args.output:
        output.close()
        print(f"\nWrote results to {args.output}")


if __name__ == '__main__':
    main()
