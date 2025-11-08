# Internal Project Notes

Quick reference for navigating scattered work across multiple folders.

## Active Project Locations

### 1. Main Clustering Code (THIS REPO)
**Location:** `/Users/jim-spencer/git/javaMap/`

**What it does:** Hierarchical clustering of US census data using gravitational potential

**Key files:**
- `src/com/jimspencer/Tracts.java` - Main clustering algorithm with caching
- `src/com/jimspencer/Tract.java` - Individual tract/merged region
- `src/com/jimspencer/SpiderMap.java` - Alternative edge-based approach
- `res/censusTracts.csv` - Input: ~74k US census tracts
- `res/treeOutput.csv` - Output: sequential merge records
- `res/74k_us.pdf` - Spider web visualization
- `res/usa6region.jpg` - Physical map with hand-drawn 6 regions

**Status:** Working code, generates visualizations. Needs cleanup/tests.

---

### 2. Gridded Potential Surface Generator
**Location:** `/Users/jim-spencer/Google Drive/My Drive/gridded/`

**What it does:** Calculates gravitational potential field on a grid (for 3D surface visualization)

**Key files:**
- `src/com/jimspencer/Main.java` - Reads population grid, calculates potential at each point
- `src/com/jimspencer/PopPoint.java` - Grid point with potential value
- `res/gpw_v4_population_count_adjusted_to_2015_unwpp_country_totals_rev11_2020_15_min.asc` - World population grid (15-arcmin resolution)
- `res/newPot3.csv` - **IMPORTANT:** 64MB output with lat/lon/potential for 3D rendering
- `other old stuff/1degmm.obj` - Example 3D wavefront file

**Algorithm:**
```java
for each grid point (lat, lon):
    potential = Σ(pop[i] / distance(lat, lon, i)) for all population points
```

**Status:** Complete. newPot3.csv is the definitive potential field data.

**External tools used:**
- Graphing Calculator 3D Pro ($200) - converts CSV to 3D surface
- Runiter - alternative 3D rendering

**Output:** `res/3dsurface.png` (this repo) - rendered view of Western Hemisphere

---

### 3. Map One Over X
**Location:** `/Users/jim-spencer/Google Drive/My Drive/map one over x/`

**What it does:** Similar potential calculations, various datasets

**Key files:**
- `src/com/jimspencer/Cities.java` - Potential field for cities
- `res/CACensus.csv` - California census data
- `res/oneDegree.csv` - 1-degree resolution grid

**Status:** Experimental/alternate approach. May have overlapping functionality with gridded/.

---

### 4. World Data & Visualizations
**Location:** `/Users/jim-spencer/Google Drive/My Drive/` (root)

**Important files:**
- `world tree.docx` - **HAND-ANNOTATED** world hierarchy down to 3M population
- `world tree lines` - JavaScript array of merge line coordinates for web rendering
- `world 15 sec spider.json` - GeoJSON spider web (7.6MB)
- `worldPrintMap.pdf` - **THE BIG ONE** - colored world spider web map
- `world3dwavefront.mtl` - Material file for 3D surface (but .obj missing?)
- `67601 us census tracts best.json` - US spider web GeoJSON
- `67601 us census tracts best.pdf` - US spider web PDF

**Also in My Drive:**
- `javaMap/` - Possibly older version of this project?
- `74k us pop and edges/` - Related US data?

---

## Data File Quick Reference

### Input Data Formats

**CSV format (census tracts/grid cells):**
```
LONGITUDE,LATITUDE,POPULATION
-81.792589,24.550157,838
```

**GPW ASCII grid format:**
```
ncols         1440
nrows         720
xllcorner     -180.0
yllcorner     -90.0
cellsize      0.25
NODATA_value  -9999
[grid of population values]
```

### Output Data Formats

**Tree output (treeOutput.csv):**
```
count origId1 pop1 lat1 lon1 origLat1 origLon1 origId2 pop2 lat2 lon2 origLat2 origLon2
```
Each line = one merge event (chronological order)

**Potential field (newPot3.csv):**
```
A,population,lat,lon,potential
A,0.0,-89.75,-179.75,1036727.38
```

**GeoJSON (world15sec.json):**
```json
{
  "type": "Feature",
  "geometry": {
    "type": "MultiLineString",
    "coordinates": [
      [[lon1,lat1],[lon2,lat2]],
      ...
    ]
  }
}
```

**World tree lines (JavaScript):**
```js
lines.push([
  {lat: 36.23, lng: 36.12},
  {lat: 36.23, lng: 36.12}
]);
```

---

## Visualization Outputs

### Spider Web Maps
- **US**: `res/74k_us.pdf` (74k tracts, black & white)
- **US annotated**: `res/usa6region.jpg` (laminated physical map with hand-drawn regions)
- **World**: `worldPrintMap.pdf` (colored by merge order, THE SHOWPIECE)
- **World alternate**: `newMap2.jpg` (in res/ and Google Drive)

### 3D Surface
- **Rendered PNG**: `res/3dsurface.png` (Western Hemisphere view)
- **Source data**: `gridded/res/newPot3.csv` (can regenerate)

---

## Key Concepts to Remember

### Gravitational Potential Formula
```
potential(i,j) = (pop_i × pop_j) / distance(i,j)^4
```
Fourth power makes it very local (nearby matters much more than distant).

### Caching Approximation
When regions i and j merge:
```
pot(merged, k) ≈ pot(i, k) + pot(j, k)
```
Only cache if merged region >100 members (otherwise invalidate).

### Distance Calculation
Approximate spherical using cosine lookup:
```java
xMiles = deltaLon × 69.0 × cos(avgLat)
yMiles = deltaLat × 69.172
distance² = xMiles² + yMiles²
```

### Known Issues/Artifacts
1. **Equatorial grid artifact**: Early merges show horizontal bias at equator (gridded data)
   - Not visible from distance
   - Don't fix - would require major changes

2. **Line crossings**: Rare cases where spider web lines cross
   - This is CORRECT - shows potential (not geography) drives clustering
   - Feature, not bug

3. **Boundary sensitivity**: Denver/Salt Lake City flip between West/Midwest depending on:
   - Data resolution
   - Distant contributions
   - Shows genuine geographic ambiguity

---

## World Hierarchy Summary

From `world tree.docx` (manual annotation stopped at 3M pop):

1. South Asia (1.8B) - #1 biggest
2. East Asia (1.5B) - #2
3. Western Hemisphere (927M) - #3
4. Europe & Middle East (909M) - #4
5. East Africa (464M) - #5
6. West Africa (409M) - #6
7. Independent Areas (Indonesia 245M, SE Asia 109M, Philippines 103M, etc.)
8. Isolated (Australia 21M, Pacific NW 14M, etc.)

Notable sub-regions:
- Grand Trunk Road (1.1B) - Pakistan/India/Bangladesh corridor
- Mexico City region (186M)
- Nigerian Coast (130M)
- Tokyo area (44M)

Full tree continues to individual tracts/grid cells (data exists in treeOutput files).

---

## TODO / Future Work

### Code Quality
- [ ] Refactor Tracts.java (currently "ugliest code ever written")
- [ ] Add unit tests (distance, caching, merge logic)
- [ ] Extract magic numbers to constants (69.0, 100, etc.)
- [ ] Add JavaDoc comments
- [ ] Create proper README.md for public consumption

### Visualizations
- [ ] Crystal growth animation (render merge sequence chronologically)
- [ ] Interactive web viewer (click to zoom hierarchy)
- [ ] Alternative color schemes (population, distance, region membership)
- [ ] Comparison overlays (tracts vs blocks vs world grid)

### Analysis
- [ ] Verify caching accuracy (run without cache on small dataset, compare)
- [ ] Document sensitivity analysis (boundary regions)
- [ ] Statistical validation vs traditional regionalization

### Sharing
- [ ] Reddit post r/dataisbeautiful (world map)
- [ ] Blog post explaining methodology
- [ ] Observable notebook (interactive)
- [ ] Academic paper?

---

## Quick Commands

### Run US clustering:
```bash
cd /Users/jim-spencer/git/javaMap
# Compile and run Tracts.java
# Input: res/censusTracts.csv
# Output: res/treeOutput.csv
```

### Run potential field generator:
```bash
cd "/Users/jim-spencer/Google Drive/My Drive/gridded"
# Compile and run Main.java
# Input: res/gpw_v4...15_min.asc
# Output: res/newPot3.csv
```

### Convert potential CSV to 3D:
- Open newPot3.csv in Graphing Calculator 3D Pro
- Or use Runiter
- Export as .obj wavefront file
- Render/export PNG

---

## Notes to Self

- **Don't overthink the equatorial artifact** - it's cosmetic, doesn't affect regions
- **Line crossings are correct** - they show potential > geography
- **The caching is "good enough"** - cross-validation proves it
- **newPot3.csv is THE definitive potential field** - 64MB, carefully calculated
- **worldPrintMap.pdf is THE showcase piece** - colored, beautiful, complete
- **world tree.docx took forever** - manual annotation is tedious, automate next time
- **$200 on Graphing Calculator 3D Pro during COVID** - was excited about 3D printing
- **Spouse rolls eyes, printer guy thought it was cool** - they both saw the laminated map

---

## What's Actually Done vs. TODO

### ✅ DONE (Working, Validated)
- Core clustering algorithm
- US spider web (74k tracts)
- World spider web (15-arcsec grid)
- 3D potential surface generation
- World hierarchy manual annotation (to 3M)
- Cross-validation (tracts vs blocks vs world grid)
- Beautiful visualizations (PDFs, PNGs)

### ⚠️ NEEDS WORK
- Code quality (refactoring, tests, docs)
- Caching accuracy verification
- Performance optimization (adaptive distance cutoffs)

### 🎯 FUTURE (Nice to Have)
- Interactive web viewer
- Animation
- Public sharing
- Academic publication

---

## Bottom Line

**What works:** Everything. The algorithm finds real structure.
**What's ugly:** The code.
**What's missing:** Tests, docs, public release.
**What's next:** Clean up code, then decide: hobby or publication?

**The printer guy gets it.**
