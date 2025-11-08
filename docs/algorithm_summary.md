# Population Clustering & Potential Field Algorithm Summary

## Core Concept

The algorithm treats population distribution as a physical system where people attract each other through a distance-dependent force, creating natural regional hierarchies and boundaries.

## The Force Law: 1/d⁴

**Why 1/d⁴?** Scale invariance through the auction fairness argument.

Consider two regions with identical population density bidding for connections:
- **Region A**: grid size 1, population 1 per cell, cells distance 1 apart
- **Region B**: grid size 2, population 4 per cell (same density), cells distance 2 apart

For equal bidding power (no bias toward finer/coarser grids):
```
Region A bid: (1 × 1) / 1^n = 1
Region B bid: (4 × 4) / 2^n = 16 / 2^n

Setting equal: 16 / 2^n = 1 → 2^n = 16 → n = 4
```

**Result**: The 1/d⁴ force law produces consistent clustering hierarchies regardless of grid resolution.

You can mix data sources:
- World: 15 arc-minute grid (~28km)
- USA: Census tracts (~1-5km)
- Dense cities: Block groups (~0.5km)

The algorithm sees only population density and distance—it can't tell which regions came from finer data.

## Hierarchical Clustering (The Auction)

**Algorithm:**
1. Calculate pairwise potentials: `potential(i,j) = (pop_i × pop_j) / distance^4`
2. Find maximum potential connection (highest "bid")
3. Merge connected regions at closest geographic points
4. Recalculate potentials for merged region
5. Repeat until desired hierarchy emerges

**Key insight**: Regions connect where they provide/receive the most mutual value. Natural contiguity emerges through closest-point connections.

**The "sub-of-a-sub" rule** (parameter-free hierarchy):
1. For any parent cluster, sort children by population
2. Count children: 1, 2, 3, ...
3. **Stop when**: next child merged into one of the already-counted children
4. Those are the major regions
5. Recurse into each major region

No magic "top N" parameter—the structure determines N at every scale.

## Potential Field Visualization

**Purpose**: Show the "energy landscape" that drives clustering.

**Formula**: `potential(x,y) = Σ [population_i / distance_i³]`

Where:
- Potential is integrated from force: ∫(1/d⁴)dd = 1/d³
- Sum over all census tracts/grid cells
- Distance in miles with latitude correction

**Physical interpretation**:
- Population centers = deep wells (peaks in inverted view)
- Empty areas = high potential (valleys)
- Saddle points = natural regional boundaries
- "Passes" between peaks = where clustering boundaries form

## The Singularity Problem & Solution

**Problem**: Census tracts are area labels, not point masses. Treating them as points creates artificial singularities—potential explodes as distance → 0.

**Original results** (no exclusion):
- NYC: 1,789× variation within city
- LA: 6,330× variation within city
- Extreme needle-like spikes
- Unprintable, dominated by nearest-neighbor artifacts

**Solution**: 2-mile exclusion radius

Exclude all census tracts within 2 miles when calculating potential at each sample point. This treats tracts as extended area sources—you only feel their influence from outside a minimum distance.

**Results with 2-mile exclusion**:
- NYC: 40× variation (44× improvement)
- LA: 98× variation (65× improvement)
- Smooth, printable surfaces
- Major population centers clearly visible
- Natural "fog layer" effect

**Why 2 miles?**
- Roughly matches typical census tract size in urban areas
- Average nearest-neighbor distance: 0.85 miles (median)
- 2 miles excludes most immediate neighbors (~60-70%)
- Preserves broader field structure while eliminating spikes

## Sampling Strategy: Triangle Centers

**Method**:
1. Delaunay triangulation of census tract points
2. Calculate centers of triangles: `(p0 + p1 + p2) / 3`
3. Sample potential at triangle centers
4. Triangle centers naturally avoid census tract locations (no singularities)

**Advantages**:
- Follows data density (fine triangulation in cities, coarse in rural areas)
- Fast: ~73 seconds for USA (145k sample points)
- No singularities by construction
- "Lines in the desert, not on Main Street"

**Performance**: 500-900× faster than nested Python loops through NumPy vectorization

## Data Sources

### USA
- **Census tracts**: 72,539 tracts with interior point coordinates
- **Format**: CSV with LONGITUDE, LATITUDE, POPULATION
- **Resolution**: ~4,000 people per tract (variable geography)

### World
- **GPW v4 grid**: 15 arc-minute resolution (~28km at equator)
- **Coverage**: Global population distribution
- **Format**: ASCII grid, 720 × 1,440 cells

### Regional subsets
- California: 8,836 tracts
- SF Bay Area: 1,260 tracts
- Custom regions: Any CSV with lon, lat, pop

## Results & Applications

### Visualizations
- **3D potential surfaces**: Interactive HTML (Plotly)
- **Monochrome rendering**: "Peaks through fog" aesthetic
- **Multiple scales**: World → USA → California → SF Bay
- **3D printable**: 25cm × 15cm base, 2cm max height

### Regional Boundaries
The algorithm's clustering boundaries naturally align with saddle points in the potential field:
- **East Coast**: "Mountain range" with passes between Philly-NYC, Philly-DC
- **California**: Clear separation between SF Bay, Central Valley corridor, LA Basin, San Diego
- **World**: Himalayan valleys, Sahara Desert valleys, ocean barriers

### Key Insight
**The boundaries aren't programmed—they emerge from physics.** Low potential = weak connections = natural place to draw regional boundaries.

This makes the approach defensible for redistricting: boundaries respect natural "communities of interest" revealed by population gravity, not arbitrary geometric shapes.

## Technical Implementation

### Language & Tools
- **Core clustering**: Java (historical)
- **Potential calculation**: Python with NumPy (vectorized)
- **Visualization**: Plotly (interactive 3D), screenshots for presentation

### File Organization
```
javaMap/
├── res/
│   ├── censusTracts.csv           # USA census tract data
│   ├── tracts_california.csv      # Regional subsets
│   └── tracts_sf_bay.csv
├── scripts/
│   ├── 01_triangulate_usa.py      # Create triangle mesh
│   ├── 02_calculate_potential_d3_exclude_radius.py  # Calculate with exclusion
│   ├── 03_visualize_html_mesh.py  # Generate mesh viz
│   └── 04_visualize_html_surface.py  # Generate surface viz
├── output/usa/
│   ├── triangle_centers_d3_potential_2mile.csv  # Reusable data
│   └── preview_mesh_2mile.html    # Interactive viz
└── docs/
    ├── usa_pipeline.md            # Technical documentation
    └── algorithm_summary.md       # This file
```

### Performance
- **USA triangulation**: ~1 second
- **USA potential calculation**: ~2 minutes (145k sample points)
- **Visualization generation**: ~10 seconds
- **Total pipeline**: ~2.5 minutes from raw data to interactive 3D

## Physical Analogies

**The auction model**: Like economic bidding where regions compete for connections based on mutual value.

**The potential field**: Like gravitational wells where population creates "mass" that attracts.

**The clustering**: Like crystal growth where regions merge at points of strongest attraction.

**The boundaries**: Like watershed divides where water flows apart—natural separation lines.

## Philosophical Note

*"No magic numbers. Who do you think I am?"*

The algorithm has no tunable parameters:
- Force law: derived from scale invariance
- Hierarchy: emerges from sub-of-a-sub rule
- Boundaries: found by maximum potential connections
- Exclusion radius: justified by physical tract size

Everything follows from first principles. The Persian Gulf as the center of Afro-Eurasian civilization isn't programmed—it **emerges**.
