#!/usr/bin/env python3
"""
Population Potential Calculator

Calculate population potential fields from weighted point datasets.

Usage:
    python3 src/cli/calculate_potential.py <input_csv> [min_distance] [max_distance] [--jobs N] [--output FILE]

Examples:
    python3 src/cli/calculate_potential.py res/tracts_sf_bay.csv
    python3 src/cli/calculate_potential.py res/tracts_sf_bay.csv 1.0     # Smooth to 1 mile
    python3 src/cli/calculate_potential.py res/tracts_sf_bay.csv 1.0 50  # Smooth + local only
    python3 src/cli/calculate_potential.py res/blockgroups_conus.csv 0.8 --jobs 4  # Use 4 cores
    python3 src/cli/calculate_potential.py res/blockgroups_conus.csv 0.8 --jobs 4 --output output/conus_0.8mile.csv
"""
import numpy as np
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path so we can import lib
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib import io, geometry, potential


def main():
    print("Population Potential Calculator v0.1")
    print("=" * 60)

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("\nUsage: python3 calculate_potential.py <input_csv> [min_distance] [max_distance] [--jobs N] [--output FILE]")
        print("\nExamples:")
        print("  python3 calculate_potential.py res/tracts_sf_bay.csv")
        print("  python3 calculate_potential.py res/tracts_sf_bay.csv 1.0")
        print("  python3 calculate_potential.py res/tracts_sf_bay.csv 1.0 50")
        print("  python3 calculate_potential.py res/blockgroups_conus.csv 0.8 --jobs 4")
        print("  python3 calculate_potential.py res/blockgroups_conus.csv 0.8 --jobs 4 --output output/conus_0.8mile.csv")
        sys.exit(1)

    # Parse --jobs flag first to know which args to skip
    n_jobs = 1
    jobs_value = None
    for i, arg in enumerate(sys.argv):
        if arg == '--jobs' and i + 1 < len(sys.argv):
            n_jobs = int(sys.argv[i + 1])
            jobs_value = sys.argv[i + 1]

    # Parse --output flag
    output_file = None
    output_value = None
    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            output_value = sys.argv[i + 1]

    # Parse positional args (excluding flag values)
    flag_values = {jobs_value, output_value} - {None}
    args = [a for a in sys.argv[1:] if not a.startswith('--') and a not in flag_values]
    input_file = args[0]
    min_distance = float(args[1]) if len(args) > 1 else 0.0
    max_distance = float(args[2]) if len(args) > 2 else None

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
    print(f"  Parallel jobs: {n_jobs}")

    # Calculate potential using chunked method (memory-efficient)
    print("\nCalculating potential (chunked processing)...")
    potentials = potential.calculate_potential_chunked(
        lons, lats,
        lons, lats, weights,
        geometry.haversine_distance,
        force_exponent=3,
        chunk_size=1000,
        min_distance_miles=min_distance,
        max_distance_miles=max_distance,
        n_jobs=n_jobs
    )

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"  Calculation time: {elapsed:.1f} seconds")
    print(f"  Potential range: [{potentials.min():.0f}, {potentials.max():.0f}]")

    # Save output if requested
    if output_file:
        import pandas as pd
        result_df = pd.DataFrame({
            'LONGITUDE': lons,
            'LATITUDE': lats,
            'POPULATION': weights,
            'POTENTIAL': potentials
        })
        result_df.to_csv(output_file, index=False)
        print(f"\n✓ Saved results to {output_file}")
    else:
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
