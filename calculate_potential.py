#!/usr/bin/env python3
"""
Population Potential Calculator

Calculate population potential fields from weighted point datasets.

Usage:
    python3 calculate_potential.py <input_csv> [min_distance] [max_distance]

Examples:
    python3 calculate_potential.py res/tracts_sf_bay.csv
    python3 calculate_potential.py res/tracts_sf_bay.csv 1.0     # Smooth to 1 mile
    python3 calculate_potential.py res/tracts_sf_bay.csv 1.0 50  # Smooth + local only
"""
import numpy as np
import sys
from datetime import datetime
from lib import io, geometry, potential


def main():
    print("Population Potential Calculator v0.1")
    print("=" * 60)

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("\nUsage: python3 calculate_potential.py <input_csv> [min_distance] [max_distance]")
        print("\nExamples:")
        print("  python3 calculate_potential.py res/tracts_sf_bay.csv")
        print("  python3 calculate_potential.py res/tracts_sf_bay.csv 1.0")
        print("  python3 calculate_potential.py res/tracts_sf_bay.csv 1.0 50")
        sys.exit(1)

    input_file = sys.argv[1]
    min_distance = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    max_distance = float(sys.argv[3]) if len(sys.argv) > 3 else None

    # Load data
    start_time = datetime.now()
    print(f"\nLoading {input_file}...")
    df = io.load_csv(input_file)
    print(f"  Loaded {len(df)} points")

    # Extract arrays
    lons = df['LONGITUDE'].values
    lats = df['LATITUDE'].values
    weights = df['POPULATION'].values

    print(f"  Longitude range: [{lons.min():.2f}, {lons.max():.2f}]")
    print(f"  Latitude range: [{lats.min():.2f}, {lats.max():.2f}]")
    print(f"  Total population: {weights.sum():,}")

    # Show parameters
    print(f"\nParameters:")
    print(f"  Force exponent: 3 (1/d³ potential)")
    print(f"  Min distance: {min_distance} miles {'(no smoothing)' if min_distance == 0 else '(census centroid smoothing)'}")
    print(f"  Max distance: {max_distance if max_distance else 'unlimited'}")

    # Calculate potential using chunked method (memory-efficient)
    print("\nCalculating potential (chunked processing)...")
    potentials = potential.calculate_potential_chunked(
        lons, lats,
        lons, lats, weights,
        geometry.cos_corrected_distance,
        force_exponent=3,
        chunk_size=1000,
        min_distance_miles=min_distance,
        max_distance_miles=max_distance
    )

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"  Calculation time: {elapsed:.1f} seconds")
    print(f"  Potential range: [{potentials.min():.0f}, {potentials.max():.0f}]")

    # Show results (limit to 20 rows for large datasets)
    show_limit = min(20, len(df))
    print(f"\nResults (showing {show_limit} of {len(df)} points):")
    print("-" * 60)
    print(f"{'Longitude':>10} {'Latitude':>10} {'Population':>12} {'Potential':>12}")
    print("-" * 60)
    for i in range(show_limit):
        print(f"{lons[i]:>10.4f} {lats[i]:>10.4f} {weights[i]:>12,.0f} {potentials[i]:>12,.0f}")
    if len(df) > show_limit:
        print(f"  ... ({len(df) - show_limit} more rows)")
    print("-" * 60)

    print(f"\n✓ Calculation complete in {elapsed:.1f} seconds!")

if __name__ == "__main__":
    main()
