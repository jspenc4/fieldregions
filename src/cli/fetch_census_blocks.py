#!/usr/bin/env python3
"""
Fetch Census block data from Census Bureau API.

Downloads block-level population and internal point coordinates for a specified
county and converts to LONGITUDE,LATITUDE,POPULATION CSV format.

Usage:
    python3 fetch_census_blocks.py <state_fips> <county_fips> <output.csv>

Example:
    python3 fetch_census_blocks.py 36 027 res/blocks_dutchess_ny.csv
"""

import sys
import json
import urllib.request
import urllib.parse


def fetch_census_blocks(state_fips, county_fips, output_path):
    """
    Fetch Census blocks from API and save to CSV.

    Args:
        state_fips: 2-digit state FIPS code (e.g., '36' for NY)
        county_fips: 3-digit county FIPS code (e.g., '027' for Dutchess)
        output_path: Path to output CSV file
    """

    # Census API endpoint for 2020 Decennial Census (PL 94-171)
    base_url = "https://api.census.gov/data/2020/dec/pl"

    # Variables we want:
    # - P1_001N: Total population
    # - NAME: Geographic name (for debugging)
    # Note: Internal point coords are in TIGER/Line, not readily available via API

    print(f"Fetching Census blocks for state {state_fips}, county {county_fips}...")
    print(f"Using Census API: {base_url}")

    # Build query parameters
    params = {
        'get': 'NAME,P1_001N',  # Name and total population
        'for': 'block:*',  # All blocks
        'in': f'state:{state_fips} county:{county_fips}'  # Filter by state/county
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    print(f"\nFetching data from API...")
    print(f"  URL: {url[:100]}...")

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

        print(f"  Response received: {len(data)} rows")

        # First row is headers
        headers = data[0]
        rows = data[1:]

        # Find column indices
        name_idx = headers.index('NAME')
        pop_idx = headers.index('P1_001N')
        state_idx = headers.index('state')
        county_idx = headers.index('county')
        tract_idx = headers.index('tract')
        block_idx = headers.index('block')

        print(f"\nProcessing {len(rows)} blocks...")

        # Problem: API doesn't provide internal point coordinates!
        # We need to get them from TIGER/Line files
        print("\nWARNING: Census API doesn't provide internal point coordinates.")
        print("We need to fetch TIGER/Line data separately.")
        print("\nFetching TIGER/Line geometry data...")

        # TIGER/Line REST endpoint
        # Format: https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/{layer}/query
        # Layer 8 = Blocks (2020)

        tiger_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2020/MapServer/10/query"

        # Query for all blocks in this county
        tiger_params = {
            'where': f"STATE='{state_fips}' AND COUNTY='{county_fips}'",
            'outFields': 'GEOID,INTPTLAT,INTPTLON,POP100',
            'returnGeometry': 'false',
            'f': 'json',
            'resultRecordCount': 50000  # Max records per request
        }

        tiger_query_url = f"{tiger_url}?{urllib.parse.urlencode(tiger_params)}"

        print(f"  Fetching from TIGERweb...")

        with urllib.request.urlopen(tiger_query_url) as response:
            tiger_data = json.loads(response.read())

        if 'features' not in tiger_data:
            print(f"ERROR: Unexpected TIGERweb response: {tiger_data}")
            sys.exit(1)

        features = tiger_data['features']
        print(f"  Received {len(features)} blocks with coordinates")

        # Check if we hit the record limit
        if len(features) >= 50000:
            print("WARNING: May have hit API record limit (50,000). Some blocks might be missing.")
            print("Consider breaking into smaller queries by tract.")

        # Write to CSV
        with open(output_path, 'w') as f:
            f.write("LONGITUDE,LATITUDE,POPULATION\n")

            written = 0
            skipped_zero = 0

            for feature in features:
                attrs = feature['attributes']

                lon = float(attrs['INTPTLON'])
                lat = float(attrs['INTPTLAT'])
                pop = int(attrs.get('POP100', 0))

                # Skip blocks with zero population
                if pop <= 0:
                    skipped_zero += 1
                    continue

                f.write(f"{lon:.6f},{lat:.6f},{pop}\n")
                written += 1

        print(f"\nConversion complete!")
        print(f"  Written: {written:,} blocks with population > 0")
        print(f"  Skipped: {skipped_zero:,} blocks with zero population")
        print(f"  Output: {output_path}")

        # Calculate total population
        total_pop = sum(int(f['attributes'].get('POP100', 0)) for f in features)
        print(f"  Total population: {total_pop:,}")

    except urllib.error.HTTPError as e:
        print(f"\nERROR: HTTP {e.code} - {e.reason}")
        print(f"URL: {url}")
        print("\nThe Census API might be down or the query parameters are incorrect.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        print("\nCommon state/county FIPS codes:")
        print("  New York (36):")
        print("    Dutchess County: 36 027")
        print("    New York County (Manhattan): 36 061")
        print("  California (06):")
        print("    San Francisco: 06 075")
        print("    Los Angeles: 06 037")
        sys.exit(1)

    state_fips = sys.argv[1].zfill(2)  # Pad to 2 digits
    county_fips = sys.argv[2].zfill(3)  # Pad to 3 digits
    output_path = sys.argv[3]

    fetch_census_blocks(state_fips, county_fips, output_path)


if __name__ == '__main__':
    main()
