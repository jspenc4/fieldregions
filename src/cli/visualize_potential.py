#!/usr/bin/env python3
"""
Visualize population potential fields as interactive 3D HTML or static PNG.

Reads potential data from CSV and creates scatter or surface plots.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import argparse
import pandas as pd
import numpy as np
from lib.visualization import create_scatter_3d, create_surface_3d, create_mesh_3d


def detect_csv_format(df):
    """
    Auto-detect CSV format and extract lon, lat, potential columns.

    Supports various column name formats:
    - LONGITUDE, LATITUDE, POTENTIAL
    - lon, lat, potential
    - LONGITUDE, LATITUDE, POPULATION, POTENTIAL (population ignored)

    Returns:
        tuple: (lons, lats, potentials) as numpy arrays
    """
    # Normalize column names to lowercase for matching
    cols = {col.lower(): col for col in df.columns}

    # Try to find longitude column
    lon_col = None
    for name in ['longitude', 'lon', 'lng']:
        if name in cols:
            lon_col = cols[name]
            break

    # Try to find latitude column
    lat_col = None
    for name in ['latitude', 'lat']:
        if name in cols:
            lat_col = cols[name]
            break

    # Try to find potential column
    pot_col = None
    for name in ['potential', 'pot']:
        if name in cols:
            pot_col = cols[name]
            break

    if lon_col is None or lat_col is None or pot_col is None:
        raise ValueError(
            f"Could not detect required columns. Found: {list(df.columns)}\n"
            f"Need: LONGITUDE/lon, LATITUDE/lat, POTENTIAL/pot"
        )

    return df[lon_col].values, df[lat_col].values, df[pot_col].values


def main():
    parser = argparse.ArgumentParser(
        description='Visualize population potential fields as interactive 3D HTML',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Input/output
    parser.add_argument('input', help='Input CSV file with lon/lat/potential columns')
    parser.add_argument('-o', '--output', help='Output file (default: auto-generate from input)')
    parser.add_argument('-t', '--title', help='Plot title (default: auto-generate from input)')
    parser.add_argument('--png', action='store_true', help='Export as PNG instead of interactive HTML')

    # Visualization type
    parser.add_argument('--type', choices=['scatter', 'surface', 'mesh'], default='scatter',
                        help='Visualization type')

    # Appearance
    parser.add_argument('--colorscale', default='Jet',
                        help='Plotly colorscale name (Jet, Viridis, Plasma, Cividis, etc.)')
    parser.add_argument('--color-mode', choices=['linear', 'log'], default='linear',
                        help='Color scaling mode')
    parser.add_argument('--discrete-colors', type=int, metavar='N',
                        help='Use N discrete color bands (e.g., 4 for 3D printing). Overrides colorscale with percentile-based bands.')
    parser.add_argument('--marker-size', type=float, default=3.0,
                        help='Scatter plot marker size (scatter only)')
    parser.add_argument('--z-scale', type=float, default=0.08,
                        help='Height as fraction of horizontal span')
    parser.add_argument('--z-mode', choices=['linear', 'log'], default='linear',
                        help='Z-axis scaling mode (linear or log)')

    # Surface-specific options
    parser.add_argument('--grid-resolution', type=int, default=400,
                        help='Grid resolution for surface interpolation (surface only)')
    parser.add_argument('--interpolation', choices=['linear', 'cubic', 'nearest'], default='cubic',
                        help='Interpolation method (surface only)')

    # Size
    parser.add_argument('--width', type=int, help='Plot width in pixels (default: 1400 for scatter, 1200 for surface)')
    parser.add_argument('--height', type=int, help='Plot height in pixels (default: 900 for scatter, 800 for surface)')

    # High-quality rendering options
    parser.add_argument('--hq', action='store_true', help='High-quality mode (1920x1080, aspectmode=data, custom lighting)')
    parser.add_argument('--aspectmode', choices=['auto', 'data', 'manual'], default='auto',
                        help='Aspect ratio mode (auto uses manual for mesh/surface, data for HQ mode)')

    args = parser.parse_args()

    # Load CSV
    print(f"Loading {args.input}...")
    df = pd.read_csv(args.input)
    print(f"  {len(df)} rows, columns: {list(df.columns)}")

    # Auto-detect format
    lons, lats, potentials = detect_csv_format(df)
    print(f"  Detected: lon={lons.min():.2f} to {lons.max():.2f}, "
          f"lat={lats.min():.2f} to {lats.max():.2f}")
    print(f"  Potential: {potentials.min():,.0f} to {potentials.max():,.0f}")

    # Auto-generate title if not provided
    if args.title is None:
        input_name = Path(args.input).stem
        args.title = f"Population Potential Field ({input_name})"

    # Auto-generate output filename if not provided
    if args.output is None:
        input_path = Path(args.input)
        ext = 'png' if args.png else 'html'
        args.output = str(input_path.parent / f"{input_path.stem}_{args.type}.{ext}")

    # Handle discrete colors
    if args.discrete_colors:
        print(f"  Using {args.discrete_colors} discrete color bands")
        # Create discrete colorscale based on --colorscale base
        # Default to Cividis-like 4-color for 3D printing
        if args.discrete_colors == 4:
            base_colors = ['#00224e', '#00bfb3', '#fdc328', '#f1605d']  # Dark blue, cyan, yellow, red
        else:
            # Generate N evenly spaced colors from the base colorscale
            # This is a fallback - may not look great
            import plotly.express as px
            base_colors = px.colors.sample_colorscale(args.colorscale, args.discrete_colors)

        # Build discrete scale: each color spans 1/N of the range
        discrete_scale = []
        for i in range(args.discrete_colors):
            start = i / args.discrete_colors
            end = (i + 1) / args.discrete_colors
            color = base_colors[i]
            discrete_scale.append([start, color])
            discrete_scale.append([end, color])

        # Override the colorscale argument
        args.colorscale = discrete_scale

    # Handle HQ mode
    if args.hq:
        if args.width is None:
            args.width = 1920
        if args.height is None:
            args.height = 1080
        if args.aspectmode == 'auto':
            args.aspectmode = 'data'
    else:
        # Set default width/height based on type
        if args.width is None:
            args.width = 1400 if args.type == 'scatter' else 1200
        if args.height is None:
            args.height = 900 if args.type == 'scatter' else 800
        if args.aspectmode == 'auto':
            args.aspectmode = 'manual'

    # Create visualization
    print(f"\nCreating {args.type} plot...")
    if args.type == 'scatter':
        fig = create_scatter_3d(
            lons, lats, potentials,
            title=args.title,
            colorscale=args.colorscale,
            color_mode=args.color_mode,
            marker_size=args.marker_size,
            z_scale=args.z_scale,
            z_mode=args.z_mode,
            width=args.width,
            height=args.height
        )
    elif args.type == 'surface':
        fig = create_surface_3d(
            lons, lats, potentials,
            title=args.title,
            colorscale=args.colorscale,
            color_mode=args.color_mode,
            grid_resolution=args.grid_resolution,
            interpolation=args.interpolation,
            z_scale=args.z_scale,
            z_mode=args.z_mode,
            width=args.width,
            height=args.height
        )
    else:  # mesh
        fig = create_mesh_3d(
            lons, lats, potentials,
            title=args.title,
            colorscale=args.colorscale,
            color_mode=args.color_mode,
            z_scale=args.z_scale,
            z_mode=args.z_mode,
            width=args.width,
            height=args.height,
            aspectmode=args.aspectmode,
            hq=args.hq
        )

    # Save
    print(f"Saving to {args.output}...")
    if args.png:
        fig.write_image(args.output, width=args.width, height=args.height)
        print(f"\nDone! View: open {args.output}")
    else:
        fig.write_html(args.output)
        print(f"\nDone! Open in browser: open {args.output}")


if __name__ == '__main__':
    main()
