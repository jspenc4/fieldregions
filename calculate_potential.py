#!/usr/bin/env python3
"""
Population Potential Calculator

Calculate population potential fields from weighted point datasets.
See docs/design.md for full documentation.
"""
import numpy as np
from lib import io, geometry, potential


def main():
    print("Population Potential Calculator v0.1")
    print("=" * 60)

    # Load data
    print("\nLoading test_data/tiny.csv...")
    df = io.load_csv('test_data/tiny.csv')
    print(f"  Loaded {len(df)} points")

    # Extract arrays
    lons = df['LONGITUDE'].values
    lats = df['LATITUDE'].values
    weights = df['POPULATION'].values
    avg_lat = np.mean(lats)

    print(f"  Longitude range: [{lons.min():.2f}, {lons.max():.2f}]")
    print(f"  Latitude range: [{lats.min():.2f}, {lats.max():.2f}]")
    print(f"  Total population: {weights.sum():,}")

    # Calculate distances (all points to all points)
    print("\nCalculating distances...")
    distances = geometry.calculate_distances(lons, lats, lons, lats, avg_lat)
    print(f"  Distance matrix shape: {distances.shape}")

    # Calculate potential
    print("\nCalculating potential (1/d³, exclude 2 closest, 50mi cutoff)...")
    potentials = potential.calculate_potential(
        distances, weights,
        force_exponent=3,
        exclude_closest_n=2,
        max_distance_miles=50.0,
        contribution_cap=500000
    )

    print(f"  Potential range: [{potentials.min():.0f}, {potentials.max():.0f}]")

    # Show results
    print("\nResults:")
    print("-" * 60)
    print(f"{'Longitude':>10} {'Latitude':>10} {'Population':>12} {'Potential':>12}")
    print("-" * 60)
    for i in range(len(df)):
        print(f"{lons[i]:>10.4f} {lats[i]:>10.4f} {weights[i]:>12,.0f} {potentials[i]:>12,.0f}")
    print("-" * 60)

    print("\n✓ Calculation complete!")

if __name__ == "__main__":
    main()
