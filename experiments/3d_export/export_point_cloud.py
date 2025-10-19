#!/usr/bin/env python3
"""
Export potential field data as OBJ point cloud or simple vertex mesh.

For scattered census tract data. Blender can then use:
- Surface reconstruction
- Skin modifier
- Or just render as points

Usage: python3 export_point_cloud.py <input_csv> <output.obj> [--transform TYPE] [--z-scale SCALE]
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path


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
        return np.log10(potentials + 1) * z_scale
    elif transform_type == "log2":
        return np.log10(np.log10(potentials + 1) + 1) * z_scale
    elif transform_type == "sqrt":
        return np.sqrt(potentials) * z_scale
    elif transform_type == "cbrt":
        return np.cbrt(potentials) * z_scale
    elif transform_type == "raw":
        return potentials * z_scale
    else:
        return potentials * z_scale


def export_point_cloud_obj(df, output_path, transform="log", z_scale=1.0):
    """Export as OBJ point cloud (vertices only)."""
    print(f"\nExporting point cloud to {output_path}...")
    print(f"  Transform: {transform}")
    print(f"  Z-scale: {z_scale}")

    lons = df['lon'].values
    lats = df['lat'].values
    potentials = df['potential'].values

    # Transform Z values
    z_values = transform_z(potentials, transform, z_scale)

    print(f"  Z range after transform: {z_values.min():.2f} to {z_values.max():.2f}")

    with open(output_path, 'w') as f:
        f.write("# Population Gravitational Potential Point Cloud\n")
        f.write(f"# Points: {len(df)}\n")
        f.write(f"# Transform: {transform}\n")
        f.write(f"# Z-scale: {z_scale}\n\n")

        # Write vertices
        for i, (lon, lat, z) in enumerate(zip(lons, lats, z_values)):
            if i % 10000 == 0:
                print(f"  Writing vertex {i}/{len(df)}...")
            f.write(f"v {lon:.6f} {lat:.6f} {z:.6f}\n")

    print(f"✓ Exported {len(df)} vertices")
    print("\nTo use in Blender:")
    print("  1. Import → Wavefront (.obj)")
    print("  2. Select object → Edit Mode")
    print("  3. Select All (A)")
    print("  4. Mesh → Vertices → Connect Vertex Path (for simple surface)")
    print("  Or use Add-ons → Point Cloud Visualizer for rendering")


def main():
    if len(sys.argv) < 3:
        print("ERROR: Missing arguments", file=sys.stderr)
        print(file=sys.stderr)
        print("Usage: python3 export_point_cloud.py <input_csv> <output.obj> [--transform TYPE] [--z-scale SCALE]", file=sys.stderr)
        print(file=sys.stderr)
        print("Transform types: log (default), log2, sqrt, cbrt, raw", file=sys.stderr)
        print(file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  python3 export_point_cloud.py output/sf_bay_potential_d3_capped.csv output/sf_bay.obj", file=sys.stderr)
        print("  python3 export_point_cloud.py output/usa.csv output/usa.obj --transform raw --z-scale 0.00001", file=sys.stderr)
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
    export_point_cloud_obj(df, output_path, transform, z_scale)

    print()
    print("="*60)
    print("✓ Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
