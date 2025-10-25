#!/usr/bin/env python3
"""
Convert GPW Arc ASCII grid file to simple CSV format.

Reads ESRI Arc ASCII format (.asc) gridded population data and converts
to LONGITUDE,LATITUDE,POPULATION CSV format compatible with calculate_potential.py.

Usage:
    python3 convert_gpw_asc.py <input.asc> <output.csv> [--min-population N]
"""

import sys
import argparse


def convert_asc_to_csv(input_path, output_path, min_population=0):
    """
    Convert Arc ASCII grid to CSV format.

    Args:
        input_path: Path to .asc file
        output_path: Path to output CSV file
        min_population: Minimum population threshold (default: 0, include all non-zero cells)
    """
    print(f"Converting {input_path} to {output_path}")
    print(f"  Minimum population threshold: {min_population}")

    # Read header
    with open(input_path, 'r') as f:
        ncols = int(f.readline().split()[1])
        nrows = int(f.readline().split()[1])
        xllcorner = float(f.readline().split()[1])
        yllcorner = float(f.readline().split()[1])
        cellsize = float(f.readline().split()[1])
        nodata_value = float(f.readline().split()[1])

        print(f"\nGrid info:")
        print(f"  Columns: {ncols}")
        print(f"  Rows: {nrows}")
        print(f"  Total cells: {ncols * nrows:,}")
        print(f"  xllcorner: {xllcorner}")
        print(f"  yllcorner: {yllcorner}")
        print(f"  cellsize: {cellsize}")
        print(f"  NODATA: {nodata_value}")

        # Open output file
        with open(output_path, 'w') as out:
            out.write("LONGITUDE,LATITUDE,POPULATION\n")

            # Process grid data
            # Grid starts at top (north) and goes down (south)
            # First data row is northernmost
            lat = yllcorner + (nrows - 0.5) * cellsize  # Start at top, center of cell

            written_count = 0
            total_population = 0
            row_num = 0

            for line in f:
                lon = xllcorner + 0.5 * cellsize  # Start at left, center of cell
                values = line.strip().split()

                for val_str in values:
                    pop = float(val_str)

                    # Skip NODATA, zero/negative population, and cells below threshold
                    if pop != nodata_value and pop > 0 and pop >= min_population:
                        out.write(f"{lon:.6f},{lat:.6f},{pop:.0f}\n")
                        written_count += 1
                        total_population += pop

                    lon += cellsize

                lat -= cellsize  # Move south for next row
                row_num += 1

                if row_num % 100 == 0:
                    print(f"  Processed {row_num}/{nrows} rows, written {written_count:,} cells")

    print(f"\nConversion complete!")
    print(f"  Written {written_count:,} cells with population >= {min_population}")
    print(f"  Total population: {total_population:,.0f}")
    print(f"  Output: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert GPW Arc ASCII grid to CSV format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all cells with population > 0
  python3 convert_gpw_asc.py world.asc world_grid.csv

  # Only include cells with population >= 1000
  python3 convert_gpw_asc.py world.asc world_grid_1k.csv --min-population 1000
        """
    )

    parser.add_argument('input', help='Input .asc file')
    parser.add_argument('output', help='Output .csv file')
    parser.add_argument('--min-population', type=float, default=0,
                        help='Minimum population threshold (default: 0)')

    args = parser.parse_args()

    convert_asc_to_csv(args.input, args.output, args.min_population)


if __name__ == '__main__':
    main()
