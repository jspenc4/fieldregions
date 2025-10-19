#!/usr/bin/env python3
"""
Export OBJ with RAW Z-values (no log transform) but scaled for visualization.

Usage: python3 export_raw_z_obj.py <input_csv> <z_scale>
Example: python3 export_raw_z_obj.py data.csv 0.01  (1% of raw height)
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

def export_raw_obj(csv_path, output_path, z_scale=0.01, lon_range=None, lat_range=None):
    """Export surface with raw Z values scaled by z_scale."""

    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path, names=['type', 'pop', 'lat', 'lon', 'potential'])

    # Reshape to grid
    unique_lats = sorted(df['lat'].unique(), reverse=True)
    unique_lons = sorted(df['lon'].unique())
    nrows, ncols = len(unique_lats), len(unique_lons)

    lon_grid, lat_grid = np.meshgrid(unique_lons, unique_lats)
    df_sorted = df.sort_values(['lat', 'lon'], ascending=[False, True])
    potential_grid = df_sorted['potential'].values.reshape(nrows, ncols)

    # Filter to region if specified
    if lon_range or lat_range:
        lon_min, lon_max = lon_range if lon_range else (-180, 180)
        lat_min, lat_max = lat_range if lat_range else (-90, 90)

        mask = ((lon_grid >= lon_min) & (lon_grid <= lon_max) &
                (lat_grid >= lat_min) & (lat_grid <= lat_max))

        # Extract subregion
        rows, cols = np.where(mask.any(axis=1))[0], np.where(mask.any(axis=0))[0]
        if len(rows) == 0 or len(cols) == 0:
            print("ERROR: No data in specified range")
            return

        row_slice = slice(rows.min(), rows.max() + 1)
        col_slice = slice(cols.min(), cols.max() + 1)

        lon_grid = lon_grid[row_slice, col_slice]
        lat_grid = lat_grid[row_slice, col_slice]
        potential_grid = potential_grid[row_slice, col_slice]

    nrows, ncols = potential_grid.shape
    print(f"Grid: {nrows} × {ncols}")
    print(f"Potential range: {potential_grid.min():.1f} to {potential_grid.max():.1f}")

    # Use RAW potential for Z, just scaled
    z_values = potential_grid * z_scale
    print(f"Z range after scaling: {z_values.min():.3f} to {z_values.max():.3f}")

    # Write OBJ
    print(f"Writing {output_path}...")
    with open(output_path, 'w') as f:
        f.write("# Population Potential Surface (Raw Z-values)\n")
        f.write(f"# Z-scale: {z_scale} (raw potential × {z_scale})\n\n")

        # Write vertices
        vertex_map = {}
        v_idx = 1
        for i in range(nrows):
            for j in range(ncols):
                if not np.isnan(z_values[i,j]) and not np.isnan(lon_grid[i,j]):
                    f.write(f"v {lon_grid[i,j]:.6f} {lat_grid[i,j]:.6f} {z_values[i,j]:.6f}\n")
                    vertex_map[(i,j)] = v_idx
                    v_idx += 1

        f.write(f"\n# {v_idx-1} vertices\n\n")

        # Write faces
        face_count = 0
        for i in range(nrows-1):
            for j in range(ncols-1):
                if ((i,j) in vertex_map and (i,j+1) in vertex_map and
                    (i+1,j+1) in vertex_map and (i+1,j) in vertex_map):
                    v1 = vertex_map[(i,j)]
                    v2 = vertex_map[(i,j+1)]
                    v3 = vertex_map[(i+1,j+1)]
                    v4 = vertex_map[(i+1,j)]
                    f.write(f"f {v1} {v2} {v3}\n")
                    f.write(f"f {v1} {v3} {v4}\n")
                    face_count += 2

        f.write(f"\n# {face_count} faces\n")

    print(f"✓ Done! {v_idx-1} vertices, {face_count} faces")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 export_raw_z_obj.py <input_csv> [z_scale]")
        print("  z_scale: scaling factor for Z height (default 0.01)")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    z_scale = float(sys.argv[2]) if len(sys.argv) > 2 else 0.01

    output_path = Path("output/obj/western_hemisphere_raw_z.obj")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    export_raw_obj(csv_path, output_path, z_scale)
