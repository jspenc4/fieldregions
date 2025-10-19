#!/usr/bin/env python3
"""
Filter census tract CSV by bounding box to create test datasets.

Usage:
    python3 filter_tracts.py <input_csv> <region_name> <output_csv>
    python3 filter_tracts.py <input_csv> --list

Examples:
    python3 filter_tracts.py res/censusTracts.csv sf_bay res/tracts_sf_bay.csv
    python3 filter_tracts.py res/censusTracts.csv california res/tracts_california.csv
    python3 filter_tracts.py res/censusTracts.csv --list
"""

import sys
import csv
from pathlib import Path

# Predefined bounding boxes: (lon_min, lon_max, lat_min, lat_max)
REGIONS = {
    # Small test regions (~100-300 tracts) - seconds to compute
    'sf_bay': (-122.6, -121.7, 37.2, 38.0),
    'sf_peninsula': (-122.6, -122.0, 37.3, 37.8),
    'la_basin': (-118.7, -117.6, 33.6, 34.3),
    'san_diego': (-117.3, -116.9, 32.5, 33.1),
    'boston': (-71.2, -70.9, 42.2, 42.5),
    'chicago': (-87.9, -87.5, 41.6, 42.1),

    # Medium regions (~1k-3k tracts) - minutes to compute
    'bay_area_large': (-123.0, -121.0, 36.9, 38.5),
    'socal': (-119.0, -116.5, 32.5, 34.5),
    'nyc_metro': (-74.5, -73.5, 40.4, 41.0),
    'dc_metro': (-77.5, -76.8, 38.7, 39.2),

    # Large regions (~8k-15k tracts) - 10-30 minutes to compute
    'california': (-124.5, -114.0, 32.5, 42.0),
    'texas': (-106.7, -93.5, 25.8, 36.5),
    'florida': (-87.7, -80.0, 24.4, 31.0),
    'northeast': (-80.5, -66.9, 38.8, 47.5),  # DC to Maine

    # Regional groupings (~20k-40k tracts) - hours to compute
    'west_coast': (-124.6, -114.0, 32.5, 49.0),
    'east_coast': (-81.0, -66.9, 24.5, 47.5),
    'midwest': (-104.0, -80.5, 36.0, 49.0),

    # Full dataset
    'conus': (-125.0, -66.0, 24.0, 50.0),  # Continental US (excludes AK/HI)
    'all': (-180.0, 180.0, -90.0, 90.0),   # Everything
}


def filter_by_bbox(input_path: str, lon_min: float, lon_max: float,
                   lat_min: float, lat_max: float, output_path: str) -> None:
    """Filter CSV by bounding box."""

    print(f"Filtering {input_path}...")
    print(f"  Bounding box: lon [{lon_min}, {lon_max}], lat [{lat_min}, {lat_max}]")

    count_in = 0
    count_out = 0

    with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        # Copy header
        header = next(reader)
        writer.writerow(header)

        # Filter rows
        for row in reader:
            count_in += 1

            lon = float(row[0])
            lat = float(row[1])

            if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
                writer.writerow(row)
                count_out += 1

    print(f"  Input: {count_in} tracts")
    print(f"  Output: {count_out} tracts ({100*count_out/count_in:.1f}%)")
    print(f"  Saved to: {output_path}")


def list_regions():
    """Print available regions."""
    print("Available regions:")
    print()
    print("Small test regions (~100-300 tracts, seconds):")
    for name in ['sf_bay', 'sf_peninsula', 'la_basin', 'san_diego', 'boston', 'chicago']:
        bbox = REGIONS[name]
        print(f"  {name:20s} lon [{bbox[0]:7.1f}, {bbox[1]:7.1f}], lat [{bbox[2]:6.1f}, {bbox[3]:6.1f}]")

    print()
    print("Medium regions (~1k-3k tracts, minutes):")
    for name in ['bay_area_large', 'socal', 'nyc_metro', 'dc_metro']:
        bbox = REGIONS[name]
        print(f"  {name:20s} lon [{bbox[0]:7.1f}, {bbox[1]:7.1f}], lat [{bbox[2]:6.1f}, {bbox[3]:6.1f}]")

    print()
    print("Large regions (~8k-15k tracts, 10-30 minutes):")
    for name in ['california', 'texas', 'florida', 'northeast']:
        bbox = REGIONS[name]
        print(f"  {name:20s} lon [{bbox[0]:7.1f}, {bbox[1]:7.1f}], lat [{bbox[2]:6.1f}, {bbox[3]:6.1f}]")

    print()
    print("Regional groupings (~20k-40k tracts, hours):")
    for name in ['west_coast', 'east_coast', 'midwest']:
        bbox = REGIONS[name]
        print(f"  {name:20s} lon [{bbox[0]:7.1f}, {bbox[1]:7.1f}], lat [{bbox[2]:6.1f}, {bbox[3]:6.1f}]")

    print()
    print("Full datasets:")
    for name in ['conus', 'all']:
        bbox = REGIONS[name]
        print(f"  {name:20s} lon [{bbox[0]:7.1f}, {bbox[1]:7.1f}], lat [{bbox[2]:6.1f}, {bbox[3]:6.1f}]")


def main():
    if len(sys.argv) < 2:
        print("ERROR: Missing arguments", file=sys.stderr)
        print(file=sys.stderr)
        print("Usage:", file=sys.stderr)
        print("  python3 filter_tracts.py <input_csv> <region_name> <output_csv>", file=sys.stderr)
        print("  python3 filter_tracts.py <input_csv> --list", file=sys.stderr)
        print(file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  python3 filter_tracts.py res/censusTracts.csv sf_bay res/tracts_sf_bay.csv", file=sys.stderr)
        print("  python3 filter_tracts.py res/censusTracts.csv --list", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]

    # Handle --list
    if len(sys.argv) == 3 and sys.argv[2] == '--list':
        list_regions()
        return

    if len(sys.argv) < 4:
        print("ERROR: Missing arguments", file=sys.stderr)
        print("Usage: python3 filter_tracts.py <input_csv> <region_name> <output_csv>", file=sys.stderr)
        sys.exit(1)

    region_name = sys.argv[2]
    output_path = sys.argv[3]

    if not Path(input_path).exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if region_name not in REGIONS:
        print(f"ERROR: Unknown region '{region_name}'", file=sys.stderr)
        print(f"Available regions: {', '.join(REGIONS.keys())}", file=sys.stderr)
        print(f"Use --list to see bounding boxes", file=sys.stderr)
        sys.exit(1)

    bbox = REGIONS[region_name]
    filter_by_bbox(input_path, bbox[0], bbox[1], bbox[2], bbox[3], output_path)

    print()
    print("✓ Done!")


if __name__ == "__main__":
    main()
