# Population Potential Calculator - Design Document

**Version**: 1.0 (Draft)
**Date**: 2025-10-18
**Status**: Design Phase

---

## Overview

### Purpose
Calculate population potential (gravitational-like influence) for geographic point datasets. The potential at a location represents the cumulative weighted influence of all other points, attenuated by distance according to a configurable force law.

### Core Concept
For each sample point, calculate:
```
potential(p) = Σ weight(i) / distance(p, i)^n
```
Where:
- `weight(i)`: Population or other weight at source point i
- `distance(p, i)`: Distance from sample point p to source point i
- `n`: Force law exponent (typically 3 for social cohesion)

### Scope
- **Included**: Fast, flexible potential calculation with multiple sampling strategies, distance metrics, and filtering options
- **Included**: Configuration via files and/or CLI
- **Included**: Reusable for any weighted point dataset (not just census data)
- **Excluded**: Visualization (separate program)
- **Excluded**: Interactive exploration (command-line tool)

### Non-Goals
- Real-time calculation (batch processing only)
- 3D rendering (handled by separate viz tool)
- Web interface
- Database integration (CSV I/O only for now)

---

## Architecture

### Component Overview
```
┌─────────────────────────────────────────┐
│  calculate_potential.py                 │
│  (Main calculation engine)              │
│                                         │
│  Input: CSV + Config                    │
│  Output: potential.csv, metadata.json   │
└─────────────────────────────────────────┘
           │
           ├─> triangulation.csv (optional)
           └─> logs/run_YYYYMMDD_HHMMSS.log

┌─────────────────────────────────────────┐
│  visualize_potential.py                 │
│  (Future: 3D visualization)             │
│                                         │
│  Input: potential.csv + viz config      │
│  Output: interactive_viz.html           │
└─────────────────────────────────────────┘
```

### Program Structure
```
calculate_potential.py
├── main()
│   ├── parse_arguments()
│   ├── load_config()
│   ├── validate_parameters()
│   └── run_calculation()
│
├── io/
│   ├── load_input_data()
│   ├── save_potential()
│   ├── save_triangulation()
│   └── save_metadata()
│
├── geometry/
│   ├── triangulate()
│   ├── calculate_distances()
│   ├── find_neighbors()
│   └── coord_conversions()
│
├── potential/
│   ├── calculate_potential_vectorized()
│   ├── apply_distance_filters()
│   ├── apply_neighbor_exclusion()
│   └── sum_contributions()
│
└── utils/
    ├── normalize_units()
    ├── logging
    └── timing
```

### Dependencies
- **Required**:
  - `numpy`: Vectorized calculations
  - `pandas`: CSV I/O
  - `scipy.spatial`: Delaunay triangulation
  - `pyyaml`: Config file parsing

- **Optional**:
  - `pint`: Unit conversions (if we use it)
  - `pytest`: Testing framework
  - `tqdm`: Progress bars

---

## Calculation Algorithm

### High-Level Flow
```
1. Load Input Data
   ├─> Read CSV
   ├─> Validate columns
   └─> Extract lon, lat, weight arrays

2. Preprocess (Optional)
   └─> Merge nearby points to remove singularities

3. Generate Sample Points
   ├─> Option A: Use source points directly
   └─> Option B: Triangulate + use triangle centers

4. Build Spatial Index (if needed)
   └─> Delaunay triangulation for neighbor finding

5. Calculate Potential (VECTORIZED)
   For each chunk of sample points:
   ├─> Calculate distances to all source points
   ├─> Apply distance filters (exclude close, cap far)
   ├─> Calculate contributions: weight / distance^n
   ├─> Cap individual contributions
   └─> Sum → potential value

6. Save Results
   ├─> potential.csv
   ├─> triangulation.csv (if computed)
   └─> metadata.json
```

### Key Optimizations
1. **Preprocessing**: Merge nearby points to eliminate singularities
2. **Vectorization**: Process chunks of points using NumPy broadcasting
3. **Distance cutoff**: Zero contributions beyond threshold (sparse matrix)
4. **Chunking**: Process N points at a time to manage memory
5. **Early triangulation check**: Only triangulate if needed

### Distance Calculation Methods

**Geographic coordinates** (lat/lon in degrees):
- **Haversine**: True great-circle distance
  - Most accurate for Earth surface
  - Slower (~3x overhead)
  - Use for: Large regions, high precision needed

- **Cosine-corrected Euclidean**:
  - `distance = sqrt((Δlon * cos(avg_lat))² + Δlat²) * 69 miles/degree`
  - Fast, good approximation for regions < 1000 miles
  - **Default choice**

- **Simple Euclidean**:
  - `distance = sqrt(Δlon² + Δlat²)`
  - Wrong for lat/lon (distorts at high latitudes)
  - Use only for testing/debugging

**Cartesian coordinates** (flat x, y):
- Always Euclidean
- No latitude correction needed

---

## Configuration

### Parameter Categories

#### Input/Output
```yaml
input:
  file: "res/censusTracts.csv"
  lon_col: "LONGITUDE"      # Column name for X/longitude
  lat_col: "LATITUDE"       # Column name for Y/latitude
  weight_col: "POPULATION"  # Column name for weight
  coord_system: "geographic"  # or "cartesian"

output:
  dir: "output/usa_exclude2_50mi"
  save_triangulation: true
  format: "csv"  # Future: parquet, hdf5
```

#### Preprocessing
```yaml
preprocessing:
  merge_nearby: false          # Combine points at nearly identical locations
  merge_threshold: "0.01deg"   # Combine points within ~0.7 miles
  merge_method: "sum_weights"  # How to combine: sum_weights | weighted_average
```

**Purpose**: Eliminate singularities from duplicate/overlapping points
- Common in census data (multiple tracts at same centroid)
- Prevents infinite contributions when distance → 0
- Alternative to "exclude N closest" approach
- Reduces total point count (faster calculation)

#### Sampling Strategy
```yaml
sampling:
  strategy: "source_points"  # or "triangle_centers"
  # If triangle_centers:
  #   - Smoother surface
  #   - ~2x more sample points
  #   - ~2x slower
```

#### Force Law
```yaml
force:
  exponent: 3              # 1/distance^3 potential (from 1/d^4 force)
  contribution_cap: 500000 # Cap individual contributions
```

**Why 1/d³?** Derived from scale-invariance argument:
- **Force law**: 1/d⁴ ensures auction fairness across grid resolutions
- **Potential**: Integral of force → 1/d³
- **Physical interpretation**: Steeper than gravity (1/d²), emphasizes local influence
- See `docs/README.md` for full derivation

#### Distance Filters
```yaml
distance:
  # Coordinate system
  coord_system: "geographic"  # geographic | cartesian
  metric: "cos_corrected"     # haversine | cos_corrected | euclidean

  # Exclude nearby points (choose one)
  exclude_closest_n: 2          # Exclude N nearest neighbors
  # OR
  exclude_closest_ratio: 0.001  # Exclude within 0.1% of region size
  # OR
  exclude_closest_dist: "5km"   # Exclude within 5km

  # Maximum distance (choose one)
  max_distance: "50mi"          # Zero contribution beyond 50 miles
  # OR
  max_distance_ratio: 0.5       # Zero beyond 50% of region diagonal
```

#### Grid Infill (Optional)
```yaml
grid:
  enabled: false
  spacing: "2mi"              # Hexagonal grid spacing
  filter_distance: "2mi"      # Remove grid points within this distance of sources
  border_expansion_pct: 10    # Expand region bounds by 10%
```

#### Performance
```yaml
performance:
  chunk_size: 1000           # Points to process at once
  verbose: true              # Print progress
  log_file: "logs/run.log"   # Save detailed log
```

### CLI Interface

**Basic usage**:
```bash
python3 calculate_potential.py \
  --input res/censusTracts.csv \
  --output-dir output/test \
  --exclude-closest 2 \
  --max-distance 50mi
```

**Using config file**:
```bash
python3 calculate_potential.py --config experiments/usa_exclude2.yaml
```

**Hybrid (override config)**:
```bash
python3 calculate_potential.py \
  --config experiments/usa_exclude2.yaml \
  --force-exponent 4
```

**Help**:
```bash
python3 calculate_potential.py --help
```

### Default Values
```python
DEFAULTS = {
    'force_exponent': 3,
    'contribution_cap': 500000,
    'exclude_closest_n': 2,
    'max_distance': '50mi',
    'coord_system': 'geographic',
    'distance_metric': 'cos_corrected',
    'chunk_size': 1000,
    'sample_strategy': 'source_points',
    'save_triangulation': True,
}
```

---

## Input/Output Formats

### Input CSV
```csv
LONGITUDE,LATITUDE,POPULATION
-122.4194,37.7749,880000
-118.2437,34.0522,3970000
...
```

**Requirements**:
- Header row required
- Columns specified in config (default: LONGITUDE, LATITUDE, POPULATION)
- No missing values in required columns
- Weights must be non-negative

### Output: potential.csv
```csv
longitude,latitude,weight,potential
-122.4194,37.7749,880000,1234567.89
-118.2437,34.0522,3970000,9876543.21
...
```

**Columns**:
- `longitude, latitude`: Sample point coordinates
- `weight`: Original weight (if sample point is a source point), else 0
- `potential`: Calculated potential value

### Output: triangulation.csv
```csv
vertex_0,vertex_1,vertex_2
0,1,5
1,2,6
...
```

**Columns**:
- `vertex_0, vertex_1, vertex_2`: Indices into potential.csv (0-indexed)

**Only saved if**:
- Triangulation was computed (sample_strategy=triangle_centers or exclude_closest_n used)
- `save_triangulation: true` in config

### Output: metadata.json
```json
{
  "run_info": {
    "timestamp": "2025-10-18T14:30:00",
    "duration_seconds": 73.2,
    "version": "1.0.0"
  },
  "input": {
    "file": "res/censusTracts.csv",
    "num_source_points": 72043,
    "total_weight": 331449281,
    "coord_system": "geographic"
  },
  "config": {
    "force_exponent": 3,
    "exclude_closest_n": 2,
    "max_distance_mi": 50,
    "sample_strategy": "source_points"
  },
  "output": {
    "num_sample_points": 72043,
    "potential_range": [0, 3672079],
    "triangulation_computed": true,
    "num_triangles": 144059
  },
  "performance": {
    "triangulation_sec": 1.2,
    "potential_calc_sec": 71.8,
    "io_sec": 0.2
  }
}
```

---

## Distance Units & Normalization

### Philosophy
- **User interface**: Accept multiple units (km, mi, degrees, ratios)
- **Internal calculations**: Dimensionless or consistent units (degrees for geographic)
- **Display output**: Show in user-friendly units

### Unit Parsing (using Pint or similar)
```python
# User provides
max_distance = "50mi"

# Parse
distance_obj = parse_distance(max_distance, region_info)

# Convert to internal units (degrees)
max_distance_deg = distance_obj.to_degrees(avg_latitude)

# Use in calculation (dimensionless)
distances_normalized = distances_deg / region_diagonal_deg
mask = distances_normalized < max_distance_normalized
```

### Supported Unit Formats
- **Absolute**: `"50mi"`, `"80km"`, `"0.7deg"`
- **Ratio**: `"0.5ratio"` (50% of region diagonal)
- **Default**: If no unit specified, assume miles (for backward compat)

### Latitude Correction
For geographic coordinates, miles ↔ degrees conversion depends on latitude:
- 1 degree latitude ≈ 69 miles (constant)
- 1 degree longitude ≈ 69 * cos(latitude) miles (varies)

Use average latitude of region for conversions.

---

## Triangulation

### When Triangulation is Needed
1. **sample_strategy = "triangle_centers"**: Required to generate sample points
2. **exclude_closest_n > 0**: Need graph structure to find topological neighbors
3. **Visualization**: Mesh surface for 3D plots (can compute later)

### When to Skip
- **sample_strategy = "source_points"** AND **exclude_closest_dist** (geometric, not topological)

### Implementation
```python
from scipy.spatial import Delaunay

tri = Delaunay(points)  # points is Nx2 array [lon, lat]
# Returns:
#   tri.simplices: Mx3 array of vertex indices
#   tri.find_simplex(p): Find triangle containing point p
```

**Performance**: ~1 second for 70k points (USA census tracts)

### Saving Triangulation
- Save as CSV: `vertex_0, vertex_1, vertex_2`
- Or binary: `triangulation.npy` (faster load)
- Include in metadata: `num_triangles`, `avg_triangle_area`

---

## Testing Strategy

### Test Datasets

**Location**: `test_data/`

**Curated datasets**:
1. **tiny.csv**: 10 points in a line
   - Test: Basic calculation correctness
   - Expected: Known potential values

2. **grid_5x5.csv**: 25 points in regular grid
   - Test: Symmetry properties
   - Expected: Center has highest potential

3. **dense_region.csv**: NYC metro area (~5000 points)
   - Test: Dense regions, performance
   - Runtime: < 5 seconds

4. **sparse_region.csv**: Montana (~500 points)
   - Test: Sparse regions, edge cases

5. **mixed_region.csv**: California (~10k points)
   - Test: Mixed density
   - Regression: Results match validated run

### Unit Tests (pytest)

**test_io.py**:
- Load valid CSV
- Handle missing columns
- Handle malformed data
- Save/load round-trip

**test_distance.py**:
- Haversine vs cos_corrected vs euclidean
- Unit conversions (mi ↔ km ↔ deg)
- Edge cases (poles, date line)

**test_potential.py**:
- Single point (potential = 0 or self-contribution)
- Two points (analytical solution)
- Symmetry: potential(A→B) properties
- Force law exponents (1, 2, 3)

**test_triangulation.py**:
- Triangle centers calculation
- Neighbor finding
- Edge cases (colinear points)

**test_config.py**:
- Parse YAML config
- CLI argument parsing
- Parameter validation
- Defaults override

### Integration Tests

**test_end_to_end.py**:
- Run on tiny.csv → verify output files exist
- Run on grid_5x5.csv → verify symmetry
- Run with different configs → verify parameters applied

### Performance Tests

**test_performance.py**:
- Benchmark on 10k points → target < 10 seconds
- Memory usage → target < 2GB for 100k points
- Scaling: 1k, 10k, 100k points → should be ~linear

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_potential.py

# With coverage
pytest --cov=calculate_potential

# Verbose
pytest -v
```

---

## Examples

### Example 1: Minimal Usage
```bash
python3 calculate_potential.py \
  --input res/censusTracts.csv \
  --output-dir output/usa_basic
```
Uses all defaults (exclude 2 closest, 50mi cutoff, force exponent 3).

### Example 2: Custom Parameters
```bash
python3 calculate_potential.py \
  --input res/censusTracts.csv \
  --output-dir output/usa_custom \
  --exclude-closest 3 \
  --max-distance 100mi \
  --force-exponent 2
```

### Example 3: Using Config File
**File**: `experiments/usa_social_cohesion.yaml`
```yaml
input:
  file: "res/censusTracts.csv"

output:
  dir: "output/usa_social_cohesion"

force:
  exponent: 3
  contribution_cap: 500000

distance:
  exclude_closest_n: 2
  max_distance: "50mi"

performance:
  chunk_size: 1000
  verbose: true
```

**Run**:
```bash
python3 calculate_potential.py --config experiments/usa_social_cohesion.yaml
```

### Example 4: Triangle Centers for Smooth Surface
```yaml
sampling:
  strategy: "triangle_centers"  # Smoother surface, 2x slower

distance:
  exclude_closest_n: 0  # Don't exclude when using centers
  max_distance: "50mi"
```

### Example 5: Ratio-Based Distances (Scale-Free)
```yaml
distance:
  exclude_closest_ratio: 0.001  # 0.1% of region size
  max_distance_ratio: 0.5       # 50% of region diagonal
```
Same config works for SF Bay Area and entire USA.

---

## Performance Characteristics

### Expected Performance (on typical laptop)

**USA Census Tracts** (~72k points):
- Triangulation: 1 second
- Potential calc (source_points): 70 seconds
- Potential calc (triangle_centers): 150 seconds
- Total: ~75 seconds (source_points)

**Scaling**:
- Time complexity: O(N × M × C)
  - N = sample points
  - M = source points
  - C = chunk size
- Memory: O(chunk_size × M) for distance matrix
- Chunks process independently (future: parallelize)

### Optimization Opportunities (Future)
1. **Parallelization**: Process chunks in parallel (multiprocessing)
2. **Spatial indexing**: KD-tree for neighbor search (scipy.spatial.cKDTree)
3. **Sparse distance matrix**: Only compute distances < max_distance
4. **Compiled code**: Numba JIT for inner loops
5. **GPU acceleration**: CuPy for CUDA-enabled systems

**Target**: < 30 seconds for USA (70k points) with parallelization

---

## Future Work

### Performance Enhancements (v1.1)
- **Parallel processing**: Multi-core chunk processing using multiprocessing
- **Spatial indexing**: KD-tree for efficient neighbor search when max_distance is small
- **File formats**: HDF5, Parquet support for large datasets (faster I/O)

### Algorithm Enhancements (v1.2+)
- **Anisotropic distance**: Account for geographic barriers (mountains, water bodies)
- **Multi-scale calculation**: Compute at multiple distance thresholds in one pass
- **Incremental updates**: Add/remove points without full recalculation

### Integration (if demand exists)
- **GIS format support**: Read/write Shapefiles, GeoJSON
- **Jupyter notebooks**: Interactive parameter exploration and visualization

---

## References

### Mathematical Background

**Theoretical Foundation**:
- **Wilson (1970s)**: "Entropy in Urban and Regional Modelling"
  - Derived spatial interaction models from maximum entropy principle
  - Showed gravity models emerge from statistical mechanics, not physics analogy
  - Exponent β should be estimated from data, represents "friction of distance"

- **Hansen (1959)**: Accessibility models - cumulative opportunities weighted by distance
- **Harris (1954)**: Market potential - economic influence fields
- **Stewart (1948)**: "Demographic Gravitation" - early physics-inspired approach (pre-Wilson)

**Our Approach**:
- Calculate **potential field** (accessibility), not flows (Wilson's trips)
- Use **1/d³ potential** derived from 1/d⁴ force law
- **1/d⁴ justification**: Scale-invariance argument ensures consistent results across grid resolutions
- **See**: `docs/README.md` for full derivation of d⁴ exponent

**Related Fields**:
- Geographic accessibility analysis
- Spatial influence modeling
- Potential surface analysis

### Technical References
- **Delaunay Triangulation**: scipy.spatial.Delaunay documentation
- **Vectorization**: NumPy broadcasting guide
- **Unit Handling**: Pint library documentation
- **Spatial Statistics**: O'Sullivan & Unwin (2010) - "Geographic Information Analysis"

---

## Design Decisions Log

### Why sample at source_points by default?
- 2x faster than triangle_centers
- Actual data values preserved
- Sufficient for most visualization needs
- Triangle centers available if smoother surface needed

### Why exclude 2 closest neighbors?
- Removes singularities (self-contribution)
- Removes immediate neighbor artifacts
- Empirically produces smoother surfaces
- Can be disabled if raw calculation desired
- Alternative: Use `merge_nearby` preprocessing instead

### Why 50 mile cutoff?
- Balance between accuracy and performance
- Contributions beyond 50mi are negligible (for 1/d³)
- Reduces ~70% of calculations (sparse regions)
- Can be adjusted based on use case

### Why support both config files and CLI?
- **Config files**: Reproducibility, version control, documentation
- **CLI**: Quick exploration, parameter sweeps, scripting
- **Hybrid**: Override one parameter without editing file

### Why dimensionless core?
- Coordinate-system agnostic (works for lat/lon and x/y)
- Easier to test (no unit confusion)
- Flexible I/O (multiple unit systems)
- Cleaner math (no conversion bugs in core logic)

---

**Document Status**: Draft - ready for review and implementation

**Next Steps**:
1. Review design decisions
2. Implement skeleton (I/O, config parsing)
3. Implement core calculation
4. Add tests
5. Optimize performance
6. Documentation & examples
