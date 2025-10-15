# 3D Population Potential Visualization

## Overview

This document describes the 3D surface visualization approach for displaying population gravitational potential fields. Unlike the network clustering visualizations, these create continuous terrain-like surfaces where height represents population influence.

## Visual Concept

Imagine population as gravitational mass that creates "wells" in space:
- Major cities appear as tall peaks (high potential)
- Unpopulated areas are flat basins (low potential)
- The surface smoothly interpolates between population centers
- Results in Mt. Fuji-shaped peaks that are intuitive and printable

## Force Laws and Potentials

We've explored multiple physics-inspired models:

### 1. Gravity Model (1/d² force → 1/d potential)
**Use case**: Accessible explanation, 3D printing

```python
force = (pop1 * pop2) / distance²
potential = Σ(population / distance)
```

**Characteristics**:
- Long range influence (diffuse, "foggy" from above)
- Smooth, gentle peaks
- Narrow potential range: ~14× (229k to 3.2M for USA)
- Printable geometry with good height-to-width ratios
- **Rhetoric**: "This is literally gravity - the same physics that holds planets in orbit"

**Best for**:
- 3D printed models
- General audience explanations
- Physical "braille" tactile maps

### 2. Social Cohesion Model (1/d⁴ force → 1/d³ potential)
**Use case**: Precision analysis, redistricting optimization

```python
force = (pop1 * pop2) / distance⁴
potential = Σ(population / distance³)
```

**Characteristics**:
- Short range influence (sharp, localized peaks)
- Very steep falloff
- Wide potential range: infinite (0 to 4.8M for USA)
- Creates needle-thin peaks at large scales
- **Rhetoric**: "People care more about proximity than gravity does - this reflects that reality"

**Best for**:
- Interactive analysis
- Identifying tight community boundaries
- Redistricting fairness metrics
- Scale-invariant regional analysis

### 3. The Dual Presentation Strategy

Use both models complementarily:
- **Gravity (1/d²)**: Gateway drug - intuitive, printable, anchors to familiar physics
- **Social Cohesion (1/d⁴)**: Precision tool - captures the reality that proximity matters more than gravity suggests

**The soundbite**: "Put the lines in the desert, not on Main Street"

Both models support this principle - they just differ in how steeply they penalize cutting through populated areas.

## Sampling Approaches

### Triangle Center Sampling
**Fast, irregular mesh following data distribution**

```python
# 1. Triangulate census tract centroids
tri = Delaunay(census_points)

# 2. Calculate triangle centers
for triangle in tri.simplices:
    center = (p0 + p1 + p2) / 3.0

# 3. Calculate potential at each center
# 4. Re-triangulate the centers for mesh
```

**Pros**:
- Fast: ~73 seconds for USA (144k points)
- Follows data density naturally
- No singularities at census centroids

**Cons**:
- Irregular mesh can create visual artifacts
- Under/over-sampling in certain regions
- May not match reference 3D prints exactly

**Performance**: USA in 73 seconds, California in 2.3 seconds

### Gridded Sampling
**Clean, uniform mesh - matches Oct 6 western hemisphere print**

```python
# 1. Create uniform grid
lons = np.linspace(lon_min, lon_max, grid_res)
lats = np.linspace(lat_min, lat_max, grid_res)

# 2. Calculate potential at each grid point
# 3. Use grid as structured mesh
```

**Pros**:
- Uniform, clean visualization
- Better for 3D printing
- Consistent sampling density
- Matches previous successful prints

**Cons**:
- Slower (need more points for same resolution)
- Fixed sampling regardless of data density

**When to use**: Final 3D print preparation

## The Vectorization Breakthrough

### Original Implementation (Slow)
```python
# Nested Python loops with DataFrame access
for i, center in enumerate(triangle_centers):
    potential = 0.0
    for j in range(len(df)):
        d = haversine_distance(center_lat, center_lon,
                              tract_lat, tract_lon)
        potential += tract_pop / (d ** 3)
```

**Performance**:
- California: 20 minutes
- USA: Estimated 30+ hours (died at 14.6% after running all night)

### Vectorized Implementation (Fast)
```python
# Pre-extract to NumPy arrays
tract_lons = df['lon'].values
tract_lats = df['lat'].values
tract_pops = df['pop'].values

# Process in chunks
for chunk in chunks(triangle_centers, chunk_size=1000):
    # Broadcast to create all pairwise distances at once
    dlon = (center_lons[:, np.newaxis] - tract_lons[np.newaxis, :]) * cos_lat
    dlat = center_lats[:, np.newaxis] - tract_lats[np.newaxis, :]
    distances = np.sqrt(dlon**2 + dlat**2) * 69.0

    # Vectorized potential calculation
    contributions = tract_pops[np.newaxis, :] / (distances ** 3)
    potentials = np.sum(contributions, axis=1)
```

**Performance**:
- California: 2.3 seconds (500× speedup!)
- USA: 73 seconds (900× speedup!)

**Key techniques**:
1. **NumPy array pre-extraction** - eliminate DataFrame overhead
2. **Broadcasting** - `[:, np.newaxis]` creates implicit nested loops in C
3. **Chunking** - manage memory for large matrices
4. **Euclidean approximation** - 10× faster than haversine, negligible error at continental scale

**The `[:, np.newaxis]` pattern**:
```python
# Creates shape (chunk_size, 1)
center_lons[:, np.newaxis]

# Creates shape (1, num_tracts)
tract_lons[np.newaxis, :]

# Broadcasting creates shape (chunk_size, num_tracts)
dlon = center_lons[:, np.newaxis] - tract_lons[np.newaxis, :]
```

## 3D Printing Considerations

### Z-Aspect Ratio

**Scientific (proportional to region size)**:
```python
z_aspect = 0.3 * (0.79 / lat_range)  # Bay Area reference
```
- USA: 0.010 (1%)
- California: 0.027 (2.7%)
- Bay Area: 0.300 (30%)

**Problem**: Creates needle-thin peaks at national scale

**Printable (fixed for aesthetics)**:
```python
z_aspect = 0.09  # 9% like western hemisphere print
```

**Result**: Mt. Fuji shaped peaks visible from edge-on view

### The Oct 6 Western Hemisphere Print

**Observed properties**:
- Dimensions: 299 × 279 × 27 mm
- Z is ~9% of X/Y
- Beautiful Mt. Fuji shaped peaks
- Good tactile "braille map" quality

**Likely parameters** (needs verification):
- Sampling: Gridded (uniform mesh)
- Force law: 1/d² (gravity)
- Potential: 1/d
- z_aspect: 0.09 (9%)
- Cap: Unknown (probably 50k)

**Lesson learned**: ALWAYS document parameters in filename/log!

### Recommended Naming Convention

```
region_forcelaw_zaspect_cap_sampling.obj

Examples:
usa_1d2_z09_cap50k_grid.obj         # Gravity, 9% z, gridded
california_1d4_z027_cap500k_tri.obj  # Social cohesion, triangle centers
```

### 3D Printing Workflow

1. **Design phase** (triangle centers for speed):
   - Iterate on force laws, z_aspects, regions
   - Fast feedback loop (seconds to minutes)
   - Interactive HTML visualization

2. **Print preparation** (gridded for quality):
   - Switch to gridded sampling
   - Use proven parameters from design phase
   - Export to OBJ for 3D printing service or home printer

3. **Home printer advantages** ($800 investment):
   - Overnight iterations vs week-long wait
   - Break-even after ~10-15 prints
   - Enables rapid experimentation

## Color Encoding

**Interactive HTML visualizations**:
- Height: Raw potential value (direct physical meaning)
- Color: log₁₀(potential + 1) (better visual discrimination)
- Colorscale: Viridis (perceptually uniform, colorblind-friendly)

**3D Prints**:
- Monochrome (geometry tells the story)
- Shadows from lighting reveal features
- Tactile quality matters more than color
- Full-color printing available but expensive ($$$$)

## Current Scripts

### Fast Implementations (Vectorized)
- `california_triangle_centers_fast.py` - CA with 1/d³
- `usa_triangle_centers_fast.py` - USA with 1/d³
- `usa_triangle_centers_gravity.py` - USA with 1/d (scientific z_aspect)
- `usa_triangle_centers_gravity_printable.py` - USA with 1/d (9% z_aspect)

### Legacy (Slow - kept for reference)
- `usa_triangle_centers.py` - Original nested loop version

### Export Tools
- `export_3d_obj.py` - Convert to OBJ for 3D printing
- `export_delaunay_mesh.py` - Delaunay mesh export
- `export_point_cloud.py` - Point cloud format
- `generate_3d_surface.py` - Original surface generator

## Key Insights

1. **Triangle centers eliminate singularities** - No infinite potential at census tract locations

2. **Vectorization is transformative** - 500-900× speedup enables interactive exploration

3. **Force law matters for use case**:
   - 1/d² for communication and physical models
   - 1/d⁴ for technical analysis and optimization

4. **Z-aspect is aesthetic, not physical** - Match viewing angle and printing constraints

5. **Gridded vs triangle sampling** - Speed vs quality tradeoff

6. **Documentation is critical** - Always embed parameters in filenames and logs

7. **The "braille map" quality** - Tactile dimension adds value beyond visualization

## Future Work

- Gridded sampling implementation for USA
- Parameter sweep automation (test multiple force laws/z_aspects in one run)
- Direct OBJ export with embedded metadata
- Boundary overlays (state lines, districts) in 3D
- Multi-scale visualization (zoom from USA → state → metro)
- Parallel processing for gridded sampling (utilize all 14 CPU cores)

## References

**Visualization approach inspired by**:
- Gravitational potential field visualization
- Terrain rendering techniques
- Tactile map design principles

**Performance techniques from**:
- NumPy broadcasting patterns
- Scientific Python optimization practices
- Geographic data processing at scale
