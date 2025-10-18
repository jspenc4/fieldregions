#!/usr/bin/env python3
"""
Step 1: Triangulate USA census tracts and calculate triangle centers.

Input:  res/censusTracts.csv (72k census tracts: lon, lat, pop)
Output: output/usa/triangle_centers_geom.csv (~145k triangle centers: lon, lat)

Performance: ~1 second
"""

import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path
from datetime import datetime

def log(msg):
    """Print timestamped log message."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def main():
    print("="*70)
    print("USA CENSUS TRACT TRIANGULATION")
    print("="*70)
    print()

    # Load census tracts
    log("Loading census tract data...")
    input_path = Path("res/censusTracts.csv")

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        print("Expected format: LONGITUDE,LATITUDE,POPULATION")
        return 1

    df = pd.read_csv(input_path)
    log(f"Loaded {len(df):,} census tracts")

    # Extract coordinates
    points = np.column_stack((df['LONGITUDE'].values, df['LATITUDE'].values))

    # Compute Delaunay triangulation
    log("Computing Delaunay triangulation...")
    tri = Delaunay(points)
    log(f"Created {len(tri.simplices):,} triangles")

    # Calculate triangle centers
    log("Calculating triangle centers...")
    triangle_centers = []

    for i, triangle in enumerate(tri.simplices):
        if i % 50000 == 0 and i > 0:
            log(f"  Processed {i:,}/{len(tri.simplices):,} triangles...")

        p0 = points[triangle[0]]
        p1 = points[triangle[1]]
        p2 = points[triangle[2]]
        center = (p0 + p1 + p2) / 3.0
        triangle_centers.append(center)

    triangle_centers = np.array(triangle_centers)
    log(f"Calculated {len(triangle_centers):,} triangle centers")

    # Save to CSV
    output_path = Path("output/usa/triangle_centers_geom.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log(f"Saving to {output_path}...")

    # Save as lon,lat (no header)
    np.savetxt(output_path, triangle_centers, delimiter=',', fmt='%.6f')

    log(f"✓ Saved {len(triangle_centers):,} triangle centers")

    print()
    print("="*70)
    print("TRIANGULATION COMPLETE")
    print("="*70)
    print(f"Input:  {len(df):,} census tracts")
    print(f"Output: {len(triangle_centers):,} triangle centers")
    print(f"File:   {output_path}")
    print("="*70)

    return 0

if __name__ == "__main__":
    exit(main())
