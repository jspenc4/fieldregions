# USA Population Potential Pipeline

## Overview

This pipeline creates triangle-sampled population potential fields for the USA using census tract data. The output is reusable CSV data that can be visualized in multiple ways (HTML, OBJ, etc.) without recalculating the expensive potential field.

## Why Triangle Centers?

**Problem**: Calculating potential at census tract centroids creates singularities (infinite values where distance = 0).

**Solution**: Sample at Delaunay triangle centers instead:
- Triangle centers are guaranteed to NOT coincide with any census tract
- Eliminates singularities completely
- Naturally follows data density (dense triangulation in cities, sparse in rural areas)
- Fast: ~73 seconds for entire USA (145k sample points)

**The principle**: "Put the lines in the desert, not on Main Street" - artifacts appear in low-population areas, not at population centers.

## Input Data

**File**: `res/censusTracts.csv`
- **Format**: CSV with header: `LONGITUDE,LATITUDE,POPULATION`
- **Rows**: 72,539 census tracts (2020 US Census)
- **Coordinate system**: WGS84 (decimal degrees)
- **Coverage**: Continental USA (excludes Alaska, Hawaii in some analyses)

Example:
```csv
LONGITUDE,LATITUDE,POPULATION
-81.792589,24.550157,838
-81.800578,24.552255,3125
```

## Pipeline Steps

### Step 1: Triangulation

**Script**: `scripts/01_triangulate_usa.py`

**What it does**:
1. Loads census tract centroids (lon, lat)
2. Computes Delaunay triangulation
3. Calculates center point of each triangle: `(p0 + p1 + p2) / 3`
4. Saves triangle centers to CSV

**Output**: `output/usa/triangle_centers_geom.csv`
- **Format**: `lon,lat` (no header)
- **Rows**: ~144,059 triangle centers
- **Performance**: ~1 second

### Step 2: Potential Calculation

**Script**: `scripts/02_calculate_potential_d3.py`

**What it does**:
1. Loads triangle centers from Step 1
2. Loads census tract data (for populations)
3. Calculates 1/d³ potential at each triangle center using vectorized NumPy
4. Saves triangle centers with potential values

**Formula**:
```
potential(x,y) = Σ [ population_i / distance³_i ]
where distance_i = distance from (x,y) to census tract i
```

**Algorithm details**:
- Vectorized calculation (no Python loops over tracts)
- Processes triangle centers in chunks of 1000 to manage memory
- Uses latitude-corrected Euclidean distance (cos(lat) correction for longitude)
- Distance in miles: `sqrt(dlon² + dlat²) * 69.0`
- Minimum distance clamp: 0.001 miles (prevents near-singularities)
- Optional cap: 500k per contribution (prevents extreme values)

**Output**: `output/usa/triangle_centers_d3_potential.csv`
- **Format**: `lon,lat,potential` (no header)
- **Rows**: ~144,059 triangle centers
- **Potential range**: ~0.5 to ~82M (raw values, uncapped)
- **Performance**: ~72 seconds

### Total Pipeline Performance

**Complete USA calculation**: ~73 seconds
- Triangulation: ~1 sec
- Potential calculation: ~72 sec
- 500-900× faster than nested Python loops

## Output File Formats

### `triangle_centers_geom.csv`
```
-124.123,48.567
-124.089,48.542
...
```
- Pure geometry, no potential values
- Reusable for different force laws

### `triangle_centers_d3_potential.csv`
```
-124.123,48.567,42.156
-124.089,48.542,38.921
...
```
- Complete dataset: geometry + 1/d³ potential
- Ready for visualization without recalculation

## Force Law: 1/d⁴ → 1/d³ Potential

**Physical interpretation**:
- Force falls off as 1/d⁴ (steeper than gravity's 1/d²)
- Potential is the integral: ∫(1/d⁴)dd = 1/d³
- Models "social cohesion" - proximity matters more than gravity suggests

**Characteristics**:
- Short-range influence (localized peaks)
- Sharp falloff with distance
- Captures reality that people care more about nearby populations
- Creates steep peaks at cities, deep valleys in deserts

**Comparison to gravity model** (1/d² force → 1/d potential):
- Gravity: gentle, diffuse, wide influence
- Social cohesion: sharp, localized, proximity-focused
- Both support "lines in the desert" principle

## Usage Examples

### Visualize the potential field
```python
import pandas as pd
import plotly.graph_objects as go

# Load data
df = pd.read_csv('output/usa/triangle_centers_d3_potential.csv',
                 names=['lon', 'lat', 'potential'])

# Create 3D surface...
```

### Export to OBJ for 3D printing
```python
# Scale to print dimensions (25cm × 15cm × 2cm)
# Apply any Z transformation (linear, log, etc.)
# Export mesh...
```

### Calculate different force law
Reuse `triangle_centers_geom.csv` with different potential formula (1/d, 1/d², etc.)

## Reusability

**Once calculated, the triangle center potential data is reusable for**:
- Different Z scalings (linear, log, sqrt)
- Different visualizations (HTML, OBJ, PNG)
- Different color schemes
- Different camera angles
- Different base dimensions for 3D printing

**Never recalculate potential unless**:
- Census data changes
- Force law changes (1/d³ → 1/d², etc.)
- Different sampling approach needed

## File Organization

```
javaMap/
├── docs/
│   └── usa_pipeline.md          # This file
├── scripts/
│   ├── 01_triangulate_usa.py    # Step 1: Triangulation
│   └── 02_calculate_potential_d3.py  # Step 2: Potential calculation
├── res/
│   └── censusTracts.csv         # Input: 72k census tracts
└── output/usa/
    ├── triangle_centers_geom.csv         # Output 1: Geometry only
    └── triangle_centers_d3_potential.csv # Output 2: Geometry + potential
```

## Next Steps (Not Yet Implemented)

Future pipeline steps will be separate scripts:
- `03_visualize_html.py` - Generate interactive 3D HTML
- `04_export_obj.py` - Generate 3D-printable OBJ files
- `05_export_images.py` - Generate static PNG images

Each visualization script reads from the final CSV and produces different outputs without recalculating potential.
