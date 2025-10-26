#!/usr/bin/env python3
"""
Annotate peak locations with city names using reverse geocoding.

Usage:
    python3 annotate_peaks.py <input.csv> <output.txt> [--top N]
"""

import sys
import csv
import time
import urllib.request
import urllib.parse
import json


def reverse_geocode(lat, lon, prefer_english=True):
    """
    Reverse geocode using Nominatim (OpenStreetMap).

    Returns city name or None if lookup fails.
    """
    try:
        # Nominatim API (free, but rate limited to 1 req/sec)
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"

        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'PopulationPotentialAnalysis/1.0')

        # Request English names when available
        if prefer_english:
            req.add_header('Accept-Language', 'en')

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())

            # Extract city/town/village name
            address = data.get('address', {})
            city = (address.get('city') or
                   address.get('town') or
                   address.get('village') or
                   address.get('municipality') or
                   address.get('county') or
                   'Unknown')

            country = address.get('country', 'Unknown')

            return f"{city}, {country}"

    except Exception as e:
        print(f"  Geocoding failed for {lat},{lon}: {e}", file=sys.stderr)
        return None


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    print(f"Annotating top {top_n} peaks from {input_path}...")

    peaks = []
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            peaks.append({
                'lon': float(row['LONGITUDE']),
                'lat': float(row['LATITUDE']),
                'pop': int(float(row['POPULATION'])),
                'potential': float(row['POTENTIAL'])
            })

    # Sort by potential descending
    peaks.sort(key=lambda x: x['potential'], reverse=True)
    peaks = peaks[:top_n]

    print(f"Geocoding {len(peaks)} locations...")
    print("  (Rate limited to 1 request/second)")

    with open(output_path, 'w') as f:
        f.write(f"Top {top_n} Population Potential Peaks\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'Rank':<6} {'Potential':<12} {'Location':<40} {'Population':<12} {'Coordinates'}\n")
        f.write("-" * 80 + "\n")

        for i, peak in enumerate(peaks, 1):
            # Reverse geocode
            location = reverse_geocode(peak['lat'], peak['lon'])

            if location:
                line = f"{i:<6} {peak['potential']:<12.1f} {location:<40} {peak['pop']:<12,} ({peak['lat']:.3f}, {peak['lon']:.3f})\n"
            else:
                line = f"{i:<6} {peak['potential']:<12.1f} {'(geocoding failed)':<40} {peak['pop']:<12,} ({peak['lat']:.3f}, {peak['lon']:.3f})\n"

            f.write(line)
            print(line.rstrip())

            # Rate limit: 1 request per second
            if i < len(peaks):
                time.sleep(1.1)

    print(f"\n✓ Saved to {output_path}")


if __name__ == '__main__':
    main()
