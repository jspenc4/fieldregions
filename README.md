# Hierarchical Population Clustering

Gravitational potential-based clustering algorithm that discovers natural regional structure in population data at multiple scales—from neighborhoods to continents.

## Overview

This project implements a hierarchical clustering algorithm based on gravitational potential between population centers. Starting from individual census tracts or grid cells, it iteratively merges regions with the highest mutual attraction, building a complete hierarchy that reveals natural population structure without prior geographic knowledge.

**Key insight:** The same algorithm discovers both that Central Park divides Manhattan's Upper East and West Sides, and that the Sahara Desert divides North and Sub-Saharan Africa.

## Visualizations

### Spider Web Network Maps

Lines connecting merged population centers, colored by merge order.

![US Census Tracts](res/74k_us.pdf)
*74,000 US census tracts merging hierarchically*

![World Population](res/worldPrintMap.pdf)
*Global population at 15 arc-minute resolution*

### 3D Gravitational Potential Surface

Population distribution rendered as elevation, where height represents cumulative gravitational pull.

![3D Surface](res/3dsurface.png)
*Western Hemisphere gravitational potential*

## Key Findings

The algorithm naturally discovers:

- **Continental regions** (South Asia 1.8B, East Asia 1.5B, Western Hemisphere 927M)
- **Natural barriers** (deserts, oceans, mountain ranges) as low-density boundaries
- **Cultural corridors** (Grand Trunk Road in South Asia emerges as coherent 1B+ person region)
- **Metropolitan structure** (urban cores, suburbs, satellite cities)
- **Micro-geography** (Central Park divides Manhattan neighborhoods)

**Cross-validation:** Census tracts, block groups, and world grid data all converge on the same regional boundaries, confirming the algorithm captures real geographic structure.

## Algorithm

### Gravitational Potential Model

```
potential(i, j) = (population_i × population_j) / distance(i, j)^4
```

The inverse fourth power heavily weights nearby populations, mimicking urban agglomeration while allowing long-range effects.

### Process

1. Start with individual census tracts/grid cells as separate regions
2. Calculate pairwise gravitational potential between all regions
3. Merge the pair with highest potential
4. Update centroid (population-weighted) and recalculate potentials
5. Repeat until all regions merged into one

**Output:** Complete merge tree showing hierarchical structure at all scales.

### Distance Calculation

Approximate spherical distance optimized for speed:

```java
xMiles = deltaLon × 69.0 × cos(averageLatitude)
yMiles = deltaLat × 69.172
distance² = xMiles² + yMiles²
```

Cosine lookup table for latitudes 0-89° avoids repeated trig calculations.

### Performance

- **Complexity:** O(n²) with aggressive caching
- **Cache strategy:** Store potentials for large merged regions (>100 members)
- **Memory management:** Release merged tract contents to handle large datasets

## Data Sources

- **US Census Bureau:** Census tracts (~74k) and block groups (~220k)
- **GPW v4:** Gridded Population of the World (CIESIN)
  - 15 arc-minute resolution (~28km at equator, ~1 million grid cells)
  - 2015 population adjusted to UN estimates

## Project Structure

```
lib/                        # Python library
├── constants.py            # Earth distance constants
├── geometry.py             # Distance calculations (cosine-corrected, haversine)
├── potential.py            # Potential field calculation (chunked, vectorized)
└── io.py                   # CSV loading utilities

tests/                      # Python test suite
├── test_geometry.py        # Distance function tests
├── test_potential.py       # Potential calculation tests
├── test_io.py              # File I/O tests
└── test_regression.py      # Regression baselines

src/
├── cli/                    # Python CLI tools
│   ├── calculate_potential.py   # Population potential calculator
│   └── generate_3d_surface.py   # 3D visualization generator
└── com/jimspencer/         # Java implementation (original)
    ├── Tracts.java         # Main clustering algorithm with caching
    ├── Tract.java          # Individual tract or merged region
    ├── SpiderMap.java      # Alternative edge-based approach
    ├── MapEdge.java        # Adjacency between tracts
    └── Region.java         # Region merging by boundary distance

experiments/                # Experimental scripts (organized by category)
├── 3d_export/              # OBJ, STL, point cloud exports
├── 3d_print/               # Blender integration, print previews
├── triangulation/          # Delaunay triangulation utilities
├── visualization/          # Regional visualizations, color exports
├── regional_analysis/      # Specific region investigations
├── triangle_centers/       # Triangle center calculations
├── exclude_experiments/    # Exclusion parameter experiments
└── misc/                   # Utility scripts

res/
├── censusTracts.csv        # Input: US census tract data
├── treeOutput.csv          # Output: sequential merge records
├── tracts_sf_bay.csv       # SF Bay Area subset for testing
├── 74k_us.pdf              # US spider web visualization
├── worldPrintMap.pdf       # World spider web (colored)
├── 3dsurface.png           # 3D potential surface
└── usa6region.jpg          # Physical map with 6 hand-drawn regions

docs/
├── INTERNAL-NOTES.md       # Project organization reference
└── world tree.docx         # Annotated world hierarchy (to 3M pop)
```

## Usage

### Python Library (Recommended)

**Installation:**
```bash
# Install dependencies
pip install numpy scipy pandas pytest

# Run tests
pytest tests/ -v
```

**Basic Usage:**
```python
from lib import io, potential, geometry

# Load census data
df = io.load_csv('res/tracts_sf_bay.csv')
lons = df['LONGITUDE'].values
lats = df['LATITUDE'].values
weights = df['POPULATION'].values

# Calculate population potential at each census tract
# Uses 1/d³ potential (from 1/d⁴ force law)
potentials = potential.calculate_potential_chunked(
    sample_lons=lons,
    sample_lats=lats,
    source_lons=lons,
    source_lats=lats,
    source_weights=weights,
    distance_fn=geometry.cos_corrected_distance,
    force_exponent=3,
    chunk_size=1000  # Process 1000 points at a time
)

print(f"Potential range: {potentials.min():.0f} to {potentials.max():.0f}")
```

**API Reference:**

`calculate_potential_chunked(sample_lons, sample_lats, source_lons, source_lats, source_weights, distance_fn, force_exponent=3, chunk_size=1000, min_distance_miles=0.0, max_distance_miles=None)`

- **sample_lons/lats**: Where to calculate potential (e.g., triangle centers, census tracts)
- **source_lons/lats/weights**: Population sources (census tracts with populations)
- **distance_fn**: `cos_corrected_distance` (fast) or `haversine_distance` (accurate)
- **force_exponent**: 1 for gravity (1/d), 3 for social cohesion (1/d³), etc.
- **chunk_size**: Memory management (1000 works for 48GB RAM with 72k points)
- **min_distance_miles**: Smooth noise by clamping distances (e.g., 1.0 mile for census centroids)
- **max_distance_miles**: Limit to local influences (e.g., 50-100 miles)

**Distance Functions:**
- `cos_corrected_distance`: Fast approximation using cosine correction (~3× faster)
- `haversine_distance`: Accurate great-circle distance (use for scientific work)

**Smoothing Census Centroid Noise:**
```python
# Census tract centroids are approximate (±0.5-1 mile error)
# Use min_distance_miles to smooth this noise
potentials = potential.calculate_potential_chunked(
    lons, lats, lons, lats, weights,
    geometry.cos_corrected_distance,
    force_exponent=3,
    min_distance_miles=1.0  # Treat anything <1 mile as 1 mile away
)
```

**Advanced Options (pre-computed distances):**
```python
# For custom workflows, use pre-computed distance matrix
distances = geometry.cos_corrected_distance(sample_lons, sample_lats, source_lons, source_lats)
potentials = potential.calculate_potential(
    distances,
    weights,
    force_exponent=3,
    max_distance_miles=100,      # Zero contribution beyond distance
    min_distance_miles=1.0       # Smooth census noise
)
```

### Java Implementation (Original)

```bash
# Compile
javac -d out src/com/jimspencer/*.java

# Run (edit Tracts.java to select input file)
java -cp out com.jimspencer.Tracts
```

**Input:** CSV with `LONGITUDE,LATITUDE,POPULATION`
**Output:** `res/treeOutput.csv` with merge sequence

### Generating Visualizations

The tree output can be rendered as:
- GeoJSON MultiLineString for web mapping
- PDF using vector graphics tools
- Interactive visualizations (D3.js, Observable, etc.)

See `docs/INTERNAL-NOTES.md` for details on visualization workflow.

## World Population Hierarchy

Top-level structure discovered by the algorithm:

1. **South Asia** (1.8B) — Grand Trunk Road corridor, India/Pakistan/Bangladesh
2. **East Asia** (1.5B) — China, Japan, Korea
3. **Western Hemisphere** (927M) — North/Central/South America
4. **Europe & Middle East** (909M) — Benelux to Tehran, Mediterranean
5. **East Africa** (464M) — Great Lakes, Ethiopia, Mozambique corridor
6. **West Africa** (409M) — Nigerian coast, Sahel
7. **Independent Areas** — Indonesia (245M), SE Asia (109M), Philippines (103M)
8. **Isolated** — Australia (21M), Pacific Northwest (14M), New Zealand (5M)

Complete hierarchy annotated down to 3M population in `docs/world tree.docx`. The algorithm continues to individual tracts but manual annotation became tedious.

## Notable Discoveries

- **Grand Trunk Road** emerges as natural region despite spanning Pakistan/India/Bangladesh borders
- **Florida** separates from Deep South in US clustering
- **Middle East/Indian subcontinent** gap aligns with desert barrier
- **Boundary regions** (Denver, Salt Lake City) are genuinely ambiguous—they could plausibly belong to multiple regions

## Technical Notes

### Known Artifacts

**Equatorial gridding:** Early merges in gridded data show slight horizontal bias at the equator (E-W neighbors equally likely). Not visible at normal viewing distance and doesn't affect regional structure.

**Line crossings:** Spider web lines occasionally cross. This is correct—the algorithm uses potential (not pure geography) so attachment points may seem counterintuitive but reflect population attraction.

### Validation

Cross-validation across multiple datasets confirms robustness:
- US census tracts (74k)
- US block groups (220k)
- World 15 arc-minute grid (~1 million cells)

All converge on the same major regional boundaries.

## Recent Findings (2025)

### Scale Invariance Validation

Testing with US census data at different resolutions confirms the potential model is scale-invariant when using appropriate smoothing:

| Dataset | Points | NYC Peak | LA Peak | SF Peak |
|---------|--------|----------|---------|---------|
| Census Tracts | 72,539 | 511,079 | 258,125 | 226,560 |
| Block Groups | 216,273 | 509,437 | 257,986 | 226,910 |
| **Difference** | **3.0x** | **0.3%** | **0.05%** | **0.1%** |

**Key insight:** With `min_distance_miles=1.0` smoothing, increasing dataset granularity by 3× produces <1% change in results. This validates that the metric measures real population accessibility, not artifacts of census geography.

### Performance Optimizations

**Parallel Processing:** Block groups (216k × 216k = 47B calculations)
- 2 cores, no max_distance: 7.7 minutes
- 4 cores, 100-mile cutoff: 4.9 minutes (36% speedup)
- Result difference: <0.01%

**Recommendation:** Use `max_distance_miles=100` for large-scale calculations. Beyond 100 miles, contributions are negligible with force_exponent=3.

### City Rankings (1-mile smoothing)

| Rank | City | Peak Potential | Neighborhood |
|------|------|----------------|--------------|
| 1 | New York | 509,000 | Upper West Side / Yankee Stadium area |
| 2 | Los Angeles | 258,000 | Downtown LA |
| 3 | San Francisco | 227,000 | Mission District |
| 4 | Philadelphia | 188,000 | Center City / Rittenhouse Square |
| 5 | Chicago | 180,000 | Near North Side / Gold Coast |
| 6 | Boston | 175,000 | Downtown / Financial District |
| 7 | DC | 159,000 | Shaw / U Street |

**Most remote locations:** Fort McDermitt, NV and remote Montana both scored potential = 2 (vs NYC's 509,000).

### 3D Printing Plans

First physical models in progress:
- Bambu Lab P1S with AMS (4-color capability)
- Plan: Print USA map with height = population potential
- Color scheme: Blue (remote) → Cyan → Yellow → Red (dense)
- Expected print time: 12-24 hours for full USA at high detail

## Future Development

- [ ] Interactive web visualization with zoom/drill-down
- [ ] "Crystal growth" animation of merge sequence
- [ ] Temporal analysis with historical population data
- [ ] Alternative metrics (travel time, economic gravity)
- [ ] Census blocks analysis (~2.5M points, 2-3 day compute with 8 cores)
- [ ] Code refactoring and test coverage

## Contributing

This is currently a personal research project. If you're interested in collaborating, extending the work, or using it for academic research, please reach out.

## License

[To be determined]

## Citation

If you use this work, please cite:

```
Spencer, J. (2015-2021). Hierarchical Population Clustering via Gravitational Potential.
[GitHub repository or paper citation once available]
```

## Acknowledgments

Thanks to:
- The printer guy who thought it was cool
- My spouse for tolerating this obsession

---

*"It made me pretty happy, might bring joy to others."*
