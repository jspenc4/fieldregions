#!/usr/bin/env python3
"""
Investigate specific nearby points in LA with different potentials.
"""

import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist

print("Loading data...")
# Load census tracts
census_df = pd.read_csv('res/censusTracts.csv')
census_points = np.column_stack((census_df['LONGITUDE'].values, census_df['LATITUDE'].values))
census_pops = census_df['POPULATION'].values

# Load triangle centers
triangle_data = np.loadtxt('output/usa/triangle_centers_d3_potential.csv', delimiter=',')
triangle_centers = triangle_data[:, 0:2]
potentials = triangle_data[:, 2]

# Focus on South Central LA (rough bounds)
# South Central: around 33.95°N to 34.05°N, -118.35°W to -118.25°W
la_mask = (triangle_centers[:, 0] > -118.35) & (triangle_centers[:, 0] < -118.25) & \
          (triangle_centers[:, 1] > 33.95) & (triangle_centers[:, 1] < 34.05)

la_centers = triangle_centers[la_mask]
la_potentials = potentials[la_mask]

print(f"\nFound {len(la_centers)} triangle centers in South Central LA area")
print(f"Potential range: {la_potentials.min():.0f} to {la_potentials.max():.0f}")

# Find points with big potential differences that are close together
# Look for pairs with distance < 0.02 degrees (~1.4 miles) but big potential ratio

print("\nSearching for nearby points with large potential differences...")

interesting_pairs = []

for i in range(min(1000, len(la_centers))):  # Sample to avoid n² explosion
    for j in range(i+1, min(i+100, len(la_centers))):
        dist = np.linalg.norm(la_centers[i] - la_centers[j])

        if dist < 0.02:  # Within ~1.4 miles
            pot_i = la_potentials[i]
            pot_j = la_potentials[j]

            ratio = max(pot_i, pot_j) / min(pot_i, pot_j)

            if ratio > 5:  # More than 5× difference
                interesting_pairs.append({
                    'idx_i': np.where(la_mask)[0][i],
                    'idx_j': np.where(la_mask)[0][j],
                    'lon_i': la_centers[i, 0],
                    'lat_i': la_centers[i, 1],
                    'lon_j': la_centers[j, 0],
                    'lat_j': la_centers[j, 1],
                    'pot_i': pot_i,
                    'pot_j': pot_j,
                    'dist': dist * 69,  # miles
                    'ratio': ratio
                })

interesting_pairs.sort(key=lambda x: x['ratio'], reverse=True)

print(f"\nFound {len(interesting_pairs)} nearby pairs with >5× potential difference")

if interesting_pairs:
    print("\n" + "="*70)
    print("TOP 5 MOST EXTREME NEARBY PAIRS")
    print("="*70)

    for k, pair in enumerate(interesting_pairs[:5]):
        print(f"\nPair {k+1}: {pair['ratio']:.1f}× difference, {pair['dist']:.2f} miles apart")
        print(f"  Point A: ({pair['lat_i']:.5f}°N, {pair['lon_i']:.5f}°W)")
        print(f"           Potential = {pair['pot_i']:.0f}")
        print(f"           https://www.google.com/maps/@{pair['lat_i']},{pair['lon_i']},17z")
        print(f"  Point B: ({pair['lat_j']:.5f}°N, {pair['lon_j']:.5f}°W)")
        print(f"           Potential = {pair['pot_j']:.0f}")
        print(f"           https://www.google.com/maps/@{pair['lat_j']},{pair['lon_j']},17z")

        # Find nearby census tracts
        point_a = np.array([[pair['lon_i'], pair['lat_i']]])
        point_b = np.array([[pair['lon_j'], pair['lat_j']]])

        dist_a = cdist(point_a, census_points)[0]
        dist_b = cdist(point_b, census_points)[0]

        # Find 5 nearest tracts to each point
        nearest_a = np.argsort(dist_a)[:5]
        nearest_b = np.argsort(dist_b)[:5]

        print(f"\n  5 Nearest census tracts to Point A:")
        for idx in nearest_a:
            dist_miles = dist_a[idx] * 69
            print(f"    {dist_miles:.2f} mi: pop={census_pops[idx]:,} at ({census_df.iloc[idx]['LATITUDE']:.5f}, {census_df.iloc[idx]['LONGITUDE']:.5f})")

        print(f"\n  5 Nearest census tracts to Point B:")
        for idx in nearest_b:
            dist_miles = dist_b[idx] * 69
            print(f"    {dist_miles:.2f} mi: pop={census_pops[idx]:,} at ({census_df.iloc[idx]['LATITUDE']:.5f}, {census_df.iloc[idx]['LONGITUDE']:.5f})")
else:
    print("\nNo pairs found with >5× difference within 1.4 miles")

print("\n" + "="*70)
