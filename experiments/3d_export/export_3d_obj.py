#!/usr/bin/env python3
"""
Export gravitational potential surface as .obj file for 3D printing.

Reads newPot3.csv and creates a Wavefront .obj mesh with proper topology
for 3D printing (manifold, watertight surface).
"""

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
    return df

def reshape_to_grid(df):
    """Reshape 1D data into 2D grid."""
    unique_lats = sorted(df['lat'].unique(), reverse=True)
    unique_lons = sorted(df['lon'].unique())

    nrows = len(unique_lats)
    ncols = len(unique_lons)

    print(f"Grid dimensions: {nrows} rows × {ncols} cols")

    # Create meshgrid
    lon_grid, lat_grid = np.meshgrid(unique_lons, unique_lats)

    # Reshape potential values
    df_sorted = df.sort_values(['lat', 'lon'], ascending=[False, True])
    potential_grid = df_sorted['potential'].values.reshape(nrows, ncols)

    return lon_grid, lat_grid, potential_grid, unique_lons, unique_lats

def smooth_surface(grid, iterations=1, kernel_size=3):
    """
    Smooth the surface to reduce sharp peaks (better for 3D printing).

    Args:
        grid: Height grid to smooth
        iterations: Number of smoothing passes
        kernel_size: Size of smoothing kernel (3 or 5)

    Returns:
        Smoothed grid
    """
    try:
        from scipy.ndimage import uniform_filter
        smoothed = grid.copy()
        for _ in range(iterations):
            smoothed = uniform_filter(smoothed, size=kernel_size, mode='nearest')
        return smoothed
    except ImportError:
        print("Warning: scipy not available, skipping smoothing")
        return grid

def normalize_and_scale(potential_grid, base_thickness=2.0, height_scale=50.0, max_height=200.0,
                       smooth_iterations=2, min_feature_size=1.0):
    """
    Normalize potential and scale for 3D printing.

    Args:
        potential_grid: Raw potential values
        base_thickness: Minimum thickness in mm (prevents paper-thin valleys)
        height_scale: Multiplier for height variation
        max_height: Maximum height cap in mm
        smooth_iterations: Number of smoothing passes (0=no smoothing, 2=default, 4=very smooth)
        min_feature_size: Minimum feature size in mm (clamps very sharp peaks)

    Returns:
        Scaled height grid in mm
    """
    # Use log scale for better visual representation
    pot_log = np.log10(potential_grid + 1)

    # Normalize to 0-1 range
    pot_min = pot_log.min()
    pot_max = pot_log.max()
    pot_normalized = (pot_log - pot_min) / (pot_max - pot_min)

    # Apply smoothing if requested (reduces sharp spikes)
    if smooth_iterations > 0:
        print(f"Applying {smooth_iterations} smoothing passes...")
        pot_normalized = smooth_surface(pot_normalized, iterations=smooth_iterations, kernel_size=3)

    # Scale to desired height range
    heights = base_thickness + (pot_normalized * height_scale)

    # Cap maximum height
    heights = np.minimum(heights, max_height)

    # Clamp minimum feature thickness (prevents needle-thin spikes)
    if min_feature_size > 0:
        # Apply a gentle rounding to very sharp peaks
        threshold = np.percentile(heights, 98)  # Top 2% of heights
        mask = heights > threshold
        if mask.any():
            # Slightly reduce the sharpest peaks
            heights[mask] = np.maximum(heights[mask] * 0.95, threshold)

    print(f"Height range: {heights.min():.2f}mm to {heights.max():.2f}mm")

    return heights

def create_obj_mesh(lon_grid, lat_grid, height_grid, output_path,
                    lon_range=None, lat_range=None,
                    xy_scale=2.0, add_base=True):
    """
    Create Wavefront .obj file from surface data.

    Args:
        lon_grid, lat_grid, height_grid: Surface data
        output_path: Output .obj file path
        lon_range: (min, max) longitude to include (None = all)
        lat_range: (min, max) latitude to include (None = all)
        xy_scale: Horizontal scale factor in mm per degree
        add_base: If True, adds a flat base plate for stability
    """
    print(f"\nGenerating 3D mesh...")

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
        height_grid = height_grid[row_slice, col_slice]

    nrows, ncols = height_grid.shape
    print(f"Mesh grid: {nrows} × {ncols} = {nrows * ncols} vertices")

    # Scale coordinates to mm
    x_coords = lon_grid * xy_scale
    y_coords = lat_grid * xy_scale
    z_coords = height_grid

    # Shift to positive coordinates (easier for printing)
    x_coords = x_coords - x_coords.min()
    y_coords = y_coords - y_coords.min()

    print(f"Model size: {x_coords.max():.1f} × {y_coords.max():.1f} × {z_coords.max():.1f} mm")

    with open(output_path, 'w') as f:
        # Write header
        f.write("# Gravitational Potential Surface\n")
        f.write("# Generated from population clustering data\n")
        f.write(f"# Size: {x_coords.max():.1f} × {y_coords.max():.1f} × {z_coords.max():.1f} mm\n")
        f.write(f"mtllib {output_path.stem}.mtl\n")
        f.write("usemtl surface\n\n")

        # Write vertices for top surface
        vertex_count = 0
        print("Writing top surface vertices...")
        for i in range(nrows):
            for j in range(ncols):
                if not np.isnan(z_coords[i, j]):
                    f.write(f"v {x_coords[i, j]:.6f} {y_coords[i, j]:.6f} {z_coords[i, j]:.6f}\n")
                    vertex_count += 1

        base_vertex_start = vertex_count + 1

        # Write vertices for bottom base (if requested)
        if add_base:
            print("Writing base vertices...")
            for i in range(nrows):
                for j in range(ncols):
                    if not np.isnan(z_coords[i, j]):
                        f.write(f"v {x_coords[i, j]:.6f} {y_coords[i, j]:.6f} 0.0\n")
                        vertex_count += 1

        f.write(f"\n# {vertex_count} vertices\n\n")

        # Create vertex index mapping
        vertex_map = np.full((nrows, ncols), -1, dtype=int)
        vertex_idx = 1
        for i in range(nrows):
            for j in range(ncols):
                if not np.isnan(z_coords[i, j]):
                    vertex_map[i, j] = vertex_idx
                    vertex_idx += 1

        # Write faces for top surface
        print("Writing top surface faces...")
        face_count = 0
        for i in range(nrows - 1):
            for j in range(ncols - 1):
                # Check if we have all 4 corners
                v1 = vertex_map[i, j]
                v2 = vertex_map[i, j + 1]
                v3 = vertex_map[i + 1, j + 1]
                v4 = vertex_map[i + 1, j]

                if v1 > 0 and v2 > 0 and v3 > 0 and v4 > 0:
                    # Two triangles per quad
                    f.write(f"f {v1} {v2} {v3}\n")
                    f.write(f"f {v1} {v3} {v4}\n")
                    face_count += 2

        # Write faces for bottom base
        if add_base:
            print("Writing base faces...")
            for i in range(nrows - 1):
                for j in range(ncols - 1):
                    v1 = vertex_map[i, j]
                    v2 = vertex_map[i, j + 1]
                    v3 = vertex_map[i + 1, j + 1]
                    v4 = vertex_map[i + 1, j]

                    if v1 > 0 and v2 > 0 and v3 > 0 and v4 > 0:
                        # Base faces (reversed winding for downward normal)
                        b1 = v1 + base_vertex_start - 1
                        b2 = v2 + base_vertex_start - 1
                        b3 = v3 + base_vertex_start - 1
                        b4 = v4 + base_vertex_start - 1
                        f.write(f"f {b1} {b3} {b2}\n")
                        f.write(f"f {b1} {b4} {b3}\n")
                        face_count += 2

            # Write side walls to close the mesh
            print("Writing side walls...")
            # Front edge
            for j in range(ncols - 1):
                v_top1 = vertex_map[0, j]
                v_top2 = vertex_map[0, j + 1]
                if v_top1 > 0 and v_top2 > 0:
                    v_bot1 = v_top1 + base_vertex_start - 1
                    v_bot2 = v_top2 + base_vertex_start - 1
                    f.write(f"f {v_top1} {v_bot1} {v_bot2}\n")
                    f.write(f"f {v_top1} {v_bot2} {v_top2}\n")
                    face_count += 2

            # Back edge
            for j in range(ncols - 1):
                v_top1 = vertex_map[nrows - 1, j]
                v_top2 = vertex_map[nrows - 1, j + 1]
                if v_top1 > 0 and v_top2 > 0:
                    v_bot1 = v_top1 + base_vertex_start - 1
                    v_bot2 = v_top2 + base_vertex_start - 1
                    f.write(f"f {v_top1} {v_top2} {v_bot2}\n")
                    f.write(f"f {v_top1} {v_bot2} {v_bot1}\n")
                    face_count += 2

            # Left edge
            for i in range(nrows - 1):
                v_top1 = vertex_map[i, 0]
                v_top2 = vertex_map[i + 1, 0]
                if v_top1 > 0 and v_top2 > 0:
                    v_bot1 = v_top1 + base_vertex_start - 1
                    v_bot2 = v_top2 + base_vertex_start - 1
                    f.write(f"f {v_top1} {v_top2} {v_bot2}\n")
                    f.write(f"f {v_top1} {v_bot2} {v_bot1}\n")
                    face_count += 2

            # Right edge
            for i in range(nrows - 1):
                v_top1 = vertex_map[i, ncols - 1]
                v_top2 = vertex_map[i + 1, ncols - 1]
                if v_top1 > 0 and v_top2 > 0:
                    v_bot1 = v_top1 + base_vertex_start - 1
                    v_bot2 = v_top2 + base_vertex_start - 1
                    f.write(f"f {v_top1} {v_bot2} {v_top2}\n")
                    f.write(f"f {v_top1} {v_bot1} {v_bot2}\n")
                    face_count += 2

        f.write(f"\n# {face_count} faces\n")

    print(f"✓ Mesh written: {vertex_count} vertices, {face_count} faces")

    # Create companion .mtl file
    mtl_path = output_path.with_suffix('.mtl')
    with open(mtl_path, 'w') as f:
        f.write("# Material for population surface\n")
        f.write("newmtl surface\n")
        f.write("Ka 0.2 0.2 0.2\n")  # Ambient
        f.write("Kd 0.8 0.6 0.4\n")  # Diffuse (tan/earth color)
        f.write("Ks 0.1 0.1 0.1\n")  # Specular
        f.write("Ns 10.0\n")          # Shininess

    print(f"✓ Material file written: {mtl_path}")

    return vertex_count, face_count

def main():
    # Path to the potential data CSV
    import sys
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        csv_path = Path.home() / "git" / "gridded" / "res" / "newPot3.csv"

    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_path}")
        return

    # Load and process data
    df = load_potential_data(csv_path)
    lon_grid, lat_grid, potential_grid, unique_lons, unique_lats = reshape_to_grid(df)

    # Scale heights for printing
    # smooth_iterations: 0=raw/spiky, 2=moderate, 4=very smooth
    height_grid = normalize_and_scale(potential_grid,
                                      base_thickness=2.0,
                                      height_scale=50.0,
                                      max_height=150.0,
                                      smooth_iterations=2,  # Smoothing for printability
                                      min_feature_size=1.0)

    # Create output directory
    output_dir = Path("output/obj")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("GENERATING 3D PRINTABLE .OBJ FILES")
    print("="*60)

    # Generate different regional models
    models = [
        {
            'name': 'world_full',
            'lon_range': None,
            'lat_range': None,
            'xy_scale': 1.5,  # Smaller scale for full world
            'description': 'Complete world (will be LARGE - may need to scale down for printing)'
        },
        {
            'name': 'western_hemisphere',
            'lon_range': (-180, -30),
            'lat_range': (-60, 80),
            'xy_scale': 2.0,
            'description': 'Americas'
        },
        {
            'name': 'eastern_hemisphere',
            'lon_range': (-30, 180),
            'lat_range': (-60, 80),
            'xy_scale': 2.0,
            'description': 'Europe/Africa/Asia'
        },
        {
            'name': 'asia_pacific',
            'lon_range': (60, 150),
            'lat_range': (-10, 60),
            'xy_scale': 3.0,
            'description': 'Asia Pacific region'
        },
        {
            'name': 'golden_triangle',
            'lon_range': (85, 110),
            'lat_range': (15, 30),
            'xy_scale': 5.0,
            'description': 'Golden Triangle valley (Burma/Myanmar)'
        },
    ]

    for model in models:
        print(f"\n--- {model['description']} ---")
        output_path = output_dir / f"{model['name']}.obj"

        v_count, f_count = create_obj_mesh(
            lon_grid, lat_grid, height_grid,
            output_path,
            lon_range=model.get('lon_range'),
            lat_range=model.get('lat_range'),
            xy_scale=model['xy_scale'],
            add_base=False  # No base plate - allows viewing from any angle
        )

        print(f"✓ Saved: {output_path}")
        print(f"  ({v_count} vertices, {f_count} faces)")

    print("\n" + "="*60)
    print("✓ All .obj files generated!")
    print("="*60)
    print(f"\nFiles saved to: {output_dir}/")
    print("\nNext steps:")
    print("1. Open .obj files in Blender/MeshLab to preview")
    print("2. Check dimensions and scale if needed")
    print("3. Upload to 3D printing service (Shapeways, Sculpteo, etc.)")
    print("4. Or send to local makerspace/UPS Store")
    print("\nNOTE: The 'world_full' model will be very large.")
    print("      Start with a regional model for your first print!")

if __name__ == "__main__":
    main()
