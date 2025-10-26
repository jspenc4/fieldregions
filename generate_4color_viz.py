#!/usr/bin/env python3
"""
Generate 4-color discrete visualization for 3D printing preview.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from lib.visualization import create_mesh_3d

# Load data
print("Loading output/world_gpw_hex30mi_30mile_potentials.csv...")
df = pd.read_csv('output/world_gpw_hex30mi_30mile_potentials.csv')

lons = df['LONGITUDE'].values
lats = df['LATITUDE'].values
potentials = df['POTENTIAL'].values

print(f"  {len(df)} points")
print(f"  Potential range: {potentials.min():.0f} to {potentials.max():.0f}")

# Create discrete 4-color scale: blue -> cyan -> yellow -> red
# Using exact color breaks for 4 discrete bands
discrete_4color = [
    [0.00, 'rgb(0, 0, 139)'],      # dark blue
    [0.25, 'rgb(0, 0, 139)'],      # dark blue (hard edge)
    [0.25, 'rgb(0, 191, 255)'],    # cyan/deep sky blue
    [0.50, 'rgb(0, 191, 255)'],    # cyan (hard edge)
    [0.50, 'rgb(255, 255, 0)'],    # yellow
    [0.75, 'rgb(255, 255, 0)'],    # yellow (hard edge)
    [0.75, 'rgb(220, 20, 60)'],    # red/crimson
    [1.00, 'rgb(220, 20, 60)']     # red
]

print("\nCreating 4-color discrete mesh visualization...")
fig = create_mesh_3d(
    lons, lats, potentials,
    title="Population Potential Field (4-Color Discrete for 3D Printing)",
    colorscale=discrete_4color,
    color_mode='log',
    z_scale=0.05,
    width=1200,
    height=800
)

# Save PNG
print("Saving PNG...")
fig.write_image('output/world_hex30mi_30mile_print_4color_discrete.png', width=1200, height=800)
print("Done! View: open output/world_hex30mi_30mile_print_4color_discrete.png")

# Also save HTML
print("Saving HTML...")
fig.write_html('output/world_hex30mi_30mile_print_4color_discrete.html')
print("Done! View: open output/world_hex30mi_30mile_print_4color_discrete.html")
