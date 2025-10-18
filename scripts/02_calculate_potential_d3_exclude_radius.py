#!/usr/bin/env python3
"""
Step 2 (Modified): Calculate 1/d³ potential at triangle centers, EXCLUDING all tracts within 2 miles.

Treats census tracts as extended area sources - you only feel their gravitational
influence from outside a minimum radius. This prevents artificial spikes from
nearest neighbors while preserving the broader field structure.

Input:  output/usa/triangle_centers_geom.csv (~145k triangle centers: lon, lat)
        res/censusTracts.csv (72k census tracts: lon, lat, pop)
Output: output/usa/triangle_centers_d3_potential_2mile.csv (~145k: lon, lat, potential)

Performance: ~72 seconds for USA
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

def log(msg):
    """Print timestamped log message."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def main():
    print("="*70)
    print("USA 1/d³ POTENTIAL CALCULATION (EXCLUDING 2-MILE RADIUS)")
    print("="*70)
    print()

    # Load triangle centers
    log("Loading triangle centers...")
    centers_path = Path("output/usa/triangle_centers_geom.csv")

    if not centers_path.exists():
        print(f"ERROR: Triangle centers not found: {centers_path}")
        print("Run 01_triangulate_usa.py first!")
        return 1

    triangle_centers = np.loadtxt(centers_path, delimiter=',')
    log(f"Loaded {len(triangle_centers):,} triangle centers")

    # Load census tracts
    log("Loading census tract data...")
    census_path = Path("res/censusTracts.csv")

    if not census_path.exists():
        print(f"ERROR: Census data not found: {census_path}")
        return 1

    df = pd.read_csv(census_path)
    log(f"Loaded {len(df):,} census tracts")

    # Extract census tract data
    tract_lons = df['LONGITUDE'].values
    tract_lats = df['LATITUDE'].values
    tract_pops = df['POPULATION'].values

    # Calculate average latitude for longitude scaling
    avg_lat = np.mean(tract_lats)
    cos_avg_lat = np.cos(np.radians(avg_lat))

    log(f"Average latitude: {avg_lat:.2f}° (cos = {cos_avg_lat:.4f})")

    # Calculate potential at each triangle center (EXCLUDING tracts within 2 miles)
    log("")
    log("Calculating 1/d³ potential at triangle centers...")
    log("EXCLUDING all census tracts within 2 miles")
    log("Using vectorized algorithm with chunked processing")
    log("")

    EXCLUSION_RADIUS_MILES = 2.0

    potentials_at_centers = np.zeros(len(triangle_centers))
    excluded_count_total = 0

    chunk_size = 1000
    num_chunks = (len(triangle_centers) + chunk_size - 1) // chunk_size

    for chunk_idx in range(num_chunks):
        start_idx = chunk_idx * chunk_size
        end_idx = min(start_idx + chunk_size, len(triangle_centers))

        # Progress logging
        if chunk_idx % 10 == 0 or chunk_idx == num_chunks - 1:
            pct = 100 * start_idx / len(triangle_centers)
            log(f"  Processing centers {start_idx:,}/{len(triangle_centers):,} ({pct:.1f}%)")

        # Get chunk of centers
        centers_chunk = triangle_centers[start_idx:end_idx]
        center_lons = centers_chunk[:, 0]  # shape: (chunk_size,)
        center_lats = centers_chunk[:, 1]  # shape: (chunk_size,)

        # Vectorized distance calculation
        # Broadcast to get all pairwise distances: (chunk_size, num_tracts)
        dlon = (center_lons[:, np.newaxis] - tract_lons[np.newaxis, :]) * cos_avg_lat
        dlat = center_lats[:, np.newaxis] - tract_lats[np.newaxis, :]

        # Euclidean distance in scaled (lon, lat) space
        # Multiply by ~69 miles/degree
        distances = np.sqrt(dlon**2 + dlat**2) * 69.0

        # Create mask for distances > 2 miles
        valid_mask = distances > EXCLUSION_RADIUS_MILES

        # Count excluded tracts
        excluded_count_total += np.sum(~valid_mask)

        # Calculate contributions: population / distance³
        # Use np.where to zero out contributions from excluded tracts
        contributions = np.where(
            valid_mask,
            tract_pops[np.newaxis, :] / (distances ** 3),
            0.0
        )

        # Sum contributions for each center in chunk
        potentials_chunk = np.sum(contributions, axis=1)
        potentials_at_centers[start_idx:end_idx] = potentials_chunk

    avg_excluded = excluded_count_total / len(triangle_centers)

    log("")
    log(f"Excluded {excluded_count_total:,} tract-center pairs within {EXCLUSION_RADIUS_MILES} miles")
    log(f"Average {avg_excluded:.1f} tracts excluded per triangle center")
    log(f"Potential range: {potentials_at_centers.min():.2e} to {potentials_at_centers.max():.2e}")

    # Save results
    output_path = Path("output/usa/triangle_centers_d3_potential_2mile.csv")
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
    print("POTENTIAL CALCULATION COMPLETE (2-MILE EXCLUSION)")
    print("="*70)
    print(f"Input:     {len(triangle_centers):,} triangle centers")
    print(f"           {len(df):,} census tracts")
    print(f"Output:    {len(output_data):,} points with potential")
    print(f"File:      {output_path}")
    print(f"Potential: {potentials_at_centers.min():.2e} to {potentials_at_centers.max():.2e}")
    print(f"Method:    Excluded all tracts within {EXCLUSION_RADIUS_MILES} miles")
    print(f"Avg excluded: {avg_excluded:.1f} tracts per center")
    print("="*70)

    return 0

if __name__ == "__main__":
    exit(main())
