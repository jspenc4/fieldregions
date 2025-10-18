#!/usr/bin/env python3
"""Generate all regional OBJ files with raw Z-values."""

from pathlib import Path
from export_raw_z_obj import export_raw_obj

# Path to the potential data CSV
csv_path = Path.home() / "git/gridded/res/potential_1_over_d3_selfexclude/raw_potential.csv"

# Output directory
output_dir = Path("output/obj")
output_dir.mkdir(parents=True, exist_ok=True)

# Z-scale factor (0.001 = 0.1% of raw potential)
z_scale = 0.001

# Regional models
models = [
    {
        'name': 'eastern_hemisphere_raw_z',
        'lon_range': (-30, 180),
        'lat_range': (-60, 80),
        'description': 'Europe/Africa/Asia'
    },
    {
        'name': 'asia_pacific_raw_z',
        'lon_range': (60, 150),
        'lat_range': (-10, 60),
        'description': 'Asia Pacific region'
    },
    {
        'name': 'golden_triangle_raw_z',
        'lon_range': (85, 110),
        'lat_range': (15, 30),
        'description': 'Golden Triangle valley (Burma/Myanmar)'
    },
]

print("="*60)
print("GENERATING RAW Z-VALUE REGIONAL OBJ FILES")
print(f"Z-scale: {z_scale} (raw potential × {z_scale})")
print("="*60)

for model in models:
    print(f"\n{'='*60}")
    print(f"{model['name']}: {model['description']}")
    print(f"{'='*60}")

    output_path = output_dir / f"{model['name']}.obj"

    export_raw_obj(
        csv_path,
        output_path,
        z_scale=z_scale,
        lon_range=model.get('lon_range'),
        lat_range=model.get('lat_range')
    )

    print(f"✓ {model['name']}.obj complete\n")

print("\n" + "="*60)
print("ALL REGIONAL MODELS COMPLETE")
print("="*60)
