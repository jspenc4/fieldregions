#!/usr/bin/env python3
"""
Export potential field data as Delaunay triangulated mesh (OBJ format).

Uses scipy Delaunay triangulation to create a proper mesh from scattered points.

Usage: python3 export_delaunay_mesh.py <input_csv> <output.obj> [--transform TYPE] [--z-scale SCALE]
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.spatial import Delaunay


def load_potential_data(csv_path):
    """Load potential field data from CSV."""
    print(f"Loading data from {csv_path}...")

    df = pd.read_csv(csv_path,
                     names=['type', 'pop', 'lat', 'lon', 'potential'],
                     dtype={'type': str, 'pop': float, 'lat': float, 'lon': float, 'potential': float})

    print(f"Loaded {len(df)} data points")
    print(f"Potential range: {df['potential'].min():.0f} to {df['potential'].max():.0f}")

    return df


def transform_z(potentials, transform_type, z_scale):
    """Apply z transformation."""
    if transform_type == "log":
        z = np.log10(potentials + 1) * z_scale
        label = f"log₁₀(Potential) × {z_scale}"
    elif transform_type == "log2":
        z = np.log10(np.log10(potentials + 1) + 1) * z_scale
        label = f"log₁₀(log₁₀(Potential)) × {z_scale}"
    elif transform_type == "sqrt":
        z = np.sqrt(potentials) * z_scale
        label = f"√(Potential) × {z_scale}"
    elif transform_type == "cbrt":
        z = np.cbrt(potentials) * z_scale
        label = f"∛(Potential) × {z_scale}"
    elif transform_type == "raw":
        z = potentials * z_scale
        label = f"Potential × {z_scale}"
    else:
        z = potentials * z_scale
        label = f"Potential × {z_scale}"

    return z, label


def export_delaunay_mesh(df, output_path, transform="log", z_scale=1.0, xy_scale=100.0):
    """Export as OBJ with Delaunay triangulation."""
    print(f"\nExporting Delaunay mesh to {output_path}...")
    print(f"  Transform: {transform}")
    print(f"  Z-scale: {z_scale}")
    print(f"  XY-scale: {xy_scale}")

    lons = df['lon'].values * xy_scale
    lats = df['lat'].values * xy_scale
    potentials = df['potential'].values

    # Transform Z values
    z_values, z_label = transform_z(potentials, transform, z_scale)

    print(f"  Z range after transform: {z_values.min():.2f} to {z_values.max():.2f}")

    # Create 2D points for Delaunay triangulation (already scaled lon, lat)
    print("\nComputing Delaunay triangulation...")
    points_2d = np.column_stack((lons, lats))
    tri = Delaunay(points_2d)

    print(f"  Created {len(tri.simplices)} triangles")

    # Filter out triangles with long edges (removes bay/water gaps)
    # Convert miles to degrees (roughly 69 miles per degree), then scale
    max_edge_miles = 5.0  # Remove triangles with edges > 5 miles
    max_edge_degrees = max_edge_miles / 69.0
    max_edge_length = max_edge_degrees * xy_scale
    print(f"  Filtering triangles with edges > {max_edge_miles:.1f} miles ({max_edge_degrees:.3f} degrees)...")

    filtered_triangles = []
    for triangle in tri.simplices:
        # Get the three vertices
        p0 = points_2d[triangle[0]]
        p1 = points_2d[triangle[1]]
        p2 = points_2d[triangle[2]]

        # Calculate edge lengths
        edge1 = np.linalg.norm(p1 - p0)
        edge2 = np.linalg.norm(p2 - p1)
        edge3 = np.linalg.norm(p0 - p2)

        # Keep triangle only if all edges are short enough
        if edge1 <= max_edge_length and edge2 <= max_edge_length and edge3 <= max_edge_length:
            filtered_triangles.append(triangle)

    filtered_triangles = np.array(filtered_triangles)
    removed = len(tri.simplices) - len(filtered_triangles)
    print(f"  Removed {removed} long-edge triangles ({100*removed/len(tri.simplices):.1f}%)")
    print(f"  Kept {len(filtered_triangles)} triangles")

    # Write OBJ file
    print(f"\nWriting OBJ file...")
    with open(output_path, 'w') as f:
        f.write("# Population Gravitational Potential Surface\n")
        f.write(f"# Generated from Delaunay triangulation\n")
        f.write(f"# Points: {len(df)}\n")
        f.write(f"# Triangles: {len(tri.simplices)}\n")
        f.write(f"# Transform: {z_label}\n\n")

        # Write vertices (v x y z)
        for i, (lon, lat, z) in enumerate(zip(lons, lats, z_values)):
            if i % 10000 == 0 and i > 0:
                print(f"  Writing vertex {i}/{len(df)}...")
            f.write(f"v {lon:.6f} {lat:.6f} {z:.6f}\n")

        f.write(f"\n# {len(df)} vertices\n\n")

        # Write faces (f v1 v2 v3) - use filtered triangles
        # OBJ is 1-indexed, so add 1 to each vertex index
        for i, triangle in enumerate(filtered_triangles):
            if i % 10000 == 0 and i > 0:
                print(f"  Writing face {i}/{len(filtered_triangles)}...")
            v1, v2, v3 = triangle + 1  # Convert to 1-indexed
            f.write(f"f {v1} {v2} {v3}\n")

        f.write(f"\n# {len(filtered_triangles)} faces\n")

    print(f"\n✓ Exported {len(df)} vertices, {len(filtered_triangles)} faces")
    print("\nReady for Blender:")
    print("  File → Import → Wavefront (.obj)")
    print("  The mesh is already triangulated and ready to render/print!")


def main():
    if len(sys.argv) < 3:
        print("ERROR: Missing arguments", file=sys.stderr)
        print(file=sys.stderr)
        print("Usage: python3 export_delaunay_mesh.py <input_csv> <output.obj> [--transform TYPE] [--z-scale SCALE]", file=sys.stderr)
        print(file=sys.stderr)
        print("Transform types: log (default), log2, sqrt, cbrt, raw", file=sys.stderr)
        print(file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  python3 export_delaunay_mesh.py output/sf_bay_potential_d3_capped.csv output/sf_bay_mesh.obj", file=sys.stderr)
        print("  python3 export_delaunay_mesh.py output/usa.csv output/usa_mesh.obj --transform raw --z-scale 0.00001", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    # Parse optional arguments
    transform = "log"
    z_scale = 1.0

    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--transform' and i + 1 < len(sys.argv):
            transform = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--z-scale' and i + 1 < len(sys.argv):
            z_scale = float(sys.argv[i + 1])
            i += 2
        else:
            print(f"WARNING: Unknown argument: {sys.argv[i]}", file=sys.stderr)
            i += 1

    if not Path(input_path).exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Load data
    df = load_potential_data(input_path)

    # Export
    export_delaunay_mesh(df, output_path, transform, z_scale)

    print()
    print("="*60)
    print("✓ Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
