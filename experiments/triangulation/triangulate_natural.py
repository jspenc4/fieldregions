#!/usr/bin/env python3
"""
Natural Delaunay triangulation - sample potential at triangle centers only.
No artificial grid infill - completely adaptive to census tract density.
"""

import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path
import sys

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 triangulate_natural.py <input_csv> <output_dir>")
        print("Example: python3 triangulate_natural.py res/censusTracts.csv output/usa_natural")
        print("         python3 triangulate_natural.py res/tracts_sfbay.csv output/sfbay_natural")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load census data
    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    census_points = np.column_stack((df['LONGITUDE'].values, df['LATITUDE'].values))
    print(f"Loaded {len(census_points):,} census tract points")
    print(f"Total population: {df['POPULATION'].sum():,}")

    # Delaunay triangulation of ONLY census tracts
    print("\nBuilding Delaunay triangulation of census tracts...")
    tri = Delaunay(census_points)
    print(f"Created {len(tri.simplices):,} triangles")

    # Calculate triangle centers - these are our sample points
    print("\nCalculating triangle centers...")
    triangle_centers = []
    for simplex in tri.simplices:
        vertices = census_points[simplex]
        center = vertices.mean(axis=0)
        triangle_centers.append(center)

    triangle_centers = np.array(triangle_centers)
    print(f"Sample points (triangle centers): {len(triangle_centers):,}")
    print(f"Sampling density: {len(triangle_centers) / len(census_points):.2f}x census tracts")

    # Save triangle centers
    output_file = output_dir / 'triangle_centers_natural.csv'
    print(f"\nSaving to {output_file}...")
    np.savetxt(
        output_file,
        triangle_centers,
        delimiter=',',
        fmt='%.6f',
        header='longitude,latitude',
        comments=''
    )

    # Save metadata
    metadata = {
        'method': 'natural_delaunay',
        'census_tracts': len(census_points),
        'sample_points': len(triangle_centers),
        'sampling_ratio': len(triangle_centers) / len(census_points),
        'triangles': len(tri.simplices),
        'description': 'Delaunay triangulation of census tracts only, no grid infill'
    }

    import json
    metadata_file = output_dir / 'metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nDone!")
    print(f"  Triangle centers: {output_file}")
    print(f"  Metadata: {metadata_file}")

if __name__ == '__main__':
    main()
