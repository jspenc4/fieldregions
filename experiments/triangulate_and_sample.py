#!/usr/bin/env python3
"""
Natural topological approach: triangulate census tracts, sample at the tract points.
Use N-hop topological exclusion - no arbitrary distance parameters.
"""

import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path
import sys
from datetime import datetime
from collections import deque

def get_n_hop_neighbors(tri, n_hops):
    """Build adjacency graph and find N-hop neighbors for each vertex."""
    n_points = tri.points.shape[0]

    # Build adjacency list from triangulation
    adjacency = [set() for _ in range(n_points)]
    for simplex in tri.simplices:
        for i in range(3):
            for j in range(3):
                if i != j:
                    adjacency[simplex[i]].add(simplex[j])

    # BFS to find N-hop neighbors for each point
    excluded_neighbors = []
    for vertex in range(n_points):
        if vertex % 1000 == 0:
            print(f"  Building exclusion sets: {vertex:,} / {n_points:,}")

        excluded = {vertex}  # Always exclude self (0-hop)
        visited = {vertex}
        queue = deque([(vertex, 0)])

        while queue:
            current, hops = queue.popleft()
            if hops < n_hops:
                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        excluded.add(neighbor)
                        queue.append((neighbor, hops + 1))

        excluded_neighbors.append(excluded)

    return excluded_neighbors

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 triangulate_and_sample.py <input_csv> <output_dir> [n_hops]")
        print("Example: python3 triangulate_and_sample.py res/censusTracts.csv output/usa_natural 2")
        print("         python3 triangulate_and_sample.py res/tracts_sf_bay.csv output/sfbay_natural 1")
        print("\nn_hops: exclude neighbors within N graph hops (default: 1)")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_dir = Path(sys.argv[2])
    n_hops = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load census data
    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    lons = df['LONGITUDE'].values
    lats = df['LATITUDE'].values
    pops = df['POPULATION'].values
    print(f"Loaded {len(lons):,} census tract points")
    print(f"Total population: {pops.sum():,}")

    # Delaunay triangulation - defines mesh topology
    print("\nBuilding Delaunay triangulation...")
    points = np.column_stack((lons, lats))
    tri = Delaunay(points)
    print(f"Created {len(tri.simplices):,} triangles")

    # Build N-hop exclusion sets
    print(f"\nBuilding {n_hops}-hop exclusion sets...")
    excluded_neighbors = get_n_hop_neighbors(tri, n_hops)
    avg_excluded = np.mean([len(e) for e in excluded_neighbors])
    print(f"Average excluded neighbors: {avg_excluded:.1f} (including self)")

    # Calculate potential AT census tract points with topological exclusion
    print(f"\nCalculating 1/d³ potential with {n_hops}-hop exclusion...")
    print(f"Started at {datetime.now().strftime('%H:%M:%S')}")

    avg_lat = np.mean(lats)
    cos_avg_lat = np.cos(np.radians(avg_lat))

    potentials = np.zeros(len(lons))

    # Vectorized calculation with topological masking
    for i in range(len(lons)):
        if i % 500 == 0:
            progress = i / len(lons) * 100
            print(f"  Progress: {i:,} / {len(lons):,} ({progress:.1f}%)")

        # Distance from this point to all census tracts
        dlon = (lons[i] - lons) * cos_avg_lat
        dlat = lats[i] - lats
        distances = np.sqrt(dlon**2 + dlat**2) * 69.0  # miles

        # Create mask: exclude N-hop neighbors (topological, not geometric)
        valid_mask = np.ones(len(lons), dtype=bool)
        for excluded_idx in excluded_neighbors[i]:
            valid_mask[excluded_idx] = False

        # Calculate contributions from non-excluded points
        contributions = np.where(valid_mask, pops / (distances ** 3), 0.0)
        potentials[i] = np.sum(contributions)

    print(f"Finished at {datetime.now().strftime('%H:%M:%S')}")
    print(f"Potential range: {potentials.min():.2e} to {potentials.max():.2e}")
    print(f"Variation: {potentials.max() / potentials.min():.1f}×")

    # Save sample points with potential
    output_file = output_dir / 'census_tract_potential.csv'
    print(f"\nSaving to {output_file}...")
    output_data = np.column_stack((lons, lats, potentials))
    np.savetxt(
        output_file,
        output_data,
        delimiter=',',
        fmt='%.6f,%.6f,%.8e',
        header='longitude,latitude,potential',
        comments=''
    )

    # Save triangulation indices
    tri_file = output_dir / 'triangulation.csv'
    np.savetxt(
        tri_file,
        tri.simplices,
        delimiter=',',
        fmt='%d',
        header='i,j,k',
        comments=''
    )

    # Save metadata
    import json
    metadata = {
        'method': 'natural_delaunay_topological_exclusion',
        'census_tracts': len(lons),
        'sample_points': len(lons),
        'triangles': len(tri.simplices),
        'n_hops_excluded': n_hops,
        'avg_neighbors_excluded': avg_excluded,
        'potential_law': '1/d^3',
        'description': f'Delaunay triangulation of census tracts, potential sampled at tract points with {n_hops}-hop topological exclusion'
    }

    metadata_file = output_dir / 'metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nDone!")
    print(f"  Sample points: {output_file}")
    print(f"  Triangulation: {tri_file}")
    print(f"  Metadata: {metadata_file}")

if __name__ == '__main__':
    main()
