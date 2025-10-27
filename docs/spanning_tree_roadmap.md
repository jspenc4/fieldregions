# Spanning Tree Project Roadmap

## Overview

This document outlines the plan to rebuild and extend the population clustering/spanning tree work that produced the world population hierarchy.

## The Three Programs

### 1. Potential Field Calculator ✅ (COMPLETE)

**Purpose:** Calculate and visualize population potential fields using 1/d³ formula.

**Status:** Done in Python with NumPy vectorization. Used for creating 3D visualizations and identifying saddle points/boundaries.

**Location:** `src/cli/calculate_potential.py`, `src/cli/visualize_potential.py`

**Output:** Cool 3D maps showing population "energy landscape"

**Relationship to spanning tree:** The potential field (1/d³) is the integral of the auction force (1/d⁴). They're mathematically dual - same physics, different views.

---

### 2. Auction/Merger Algorithm (Tracts/SpiderMap) 🚧 (TO BE REBUILT)

**Purpose:** Run the hierarchical clustering auction to build the spanning tree showing how population regions naturally merge.

**Current Status:** Working Java implementation (`src/com/jimspencer/Tracts.java`, `SpiderMap.java`) but:
- Written "like a drunk sailor" (untested, unvalidated except "it works")
- Caching strategy is clever but not sure if optimal
- Takes hours to run on world data (218k grid cells)
- Want to rebuild properly with tests to understand it deeply

**Algorithm:**
```
1. Initialize: Each tract/cell is own region
2. Calculate all O(n²) pairwise forces: (pop_i × pop_j) / d⁴
3. Find pair with maximum mutual force (highest "bid")
4. Merge them: combine populations, calculate weighted centroid
5. Record merge: which two, populations, locations, merge order
6. Update forces between merged region and all others
7. Repeat until one global cluster remains
```

**Key insight:** This is an AUCTION where regions bid for connections based on mutual value. No parameters, no tuning. Pure physics.

**Output:** Merge sequence CSV showing every merge from individual cells → neighborhoods → cities → metros → continents → global unity.

**Example output:** `res/15sec_218500_world_results.csv` (218,500 merges)

**Visual output:** Spider maps showing geographic tree structure (see `res/74k_us.pdf`, `~/Desktop/worldReddit.png`)

---

### 3. Hierarchy Evaluator 🎯 (TO BE CREATED)

**Purpose:** Automatically extract hierarchical structure from merge sequence CSV.

**Status:** Algorithm exists conceptually and documented in `world tree.docx` (done manually). Need to implement as code.

**Input:** Merge sequence CSV from program #2

**Output:**
- Hierarchical decomposition (like `res/world tree.docx`)
- Classification of each region as:
  - **Core** - major sub-regions that form the spine
  - **Independent** - merged during parent formation but not part of a core
  - **Isolated** - merged in late, after cores were established

**Algorithm:** See `docs/hierarchy_extraction.md` for details

**Language:** Python (perfect for CSV analysis and tree manipulation)

---

## Why Rebuild Program #2 in Python?

**Current Java version concerns:**
- Not properly tested (works because "it works")
- Caching strategy untested/unvalidated
- Unclear if it's optimal for modern hardware
- Hard to experiment with different approaches

**Python advantages:**
- Easy to test and validate against Java output
- NumPy vectorization for matrix operations
- Start from first principles and understand deeply
- If too slow, we'll know exactly what needs optimization
- Can port to Rust/C++ later if needed, but with full understanding

**The multi-week journey:**

**Week 1-2: Naive O(n²) baseline**
- Pure Python, no optimization
- Calculate all pairwise forces
- Greedy merge loop
- Validate against Java on small datasets (SF tracts ~1,260 points)
- Establish correctness

**Week 3-4: Vectorization exploration**
- NumPy distance matrices
- Broadcasting for pairwise calculations
- Measure actual speedup
- Profile where time is spent

**Week 5-6: Caching decision**
- Implement the Java caching strategy in Python
- Compare: recalc with vectors vs cache lookup
- Decide which is actually faster on modern hardware
- The Java cache is clever but may not be needed with vectorization

**Week 7+: Scale and optimize**
- Multicore for initial O(n²) calculation
- Memory management for large datasets
- Scale to world (218k points)
- If still too slow, consider Rust/C++ port (but now we understand it)

**Key point:** Start slow and correct, understand deeply, optimize based on measurements. The Java version was "throw it together and it works." This time: do it right.

---

## The Visual Maps - Why They Matter

### Spider Maps Show Structure Immediately

**USA Spider Map** (`res/74k_us.pdf`):
- Dense Northeast megalopolis web
- Sparse Western plains with long connections
- Clear visual boundaries between regions
- You can SEE the 6 major US clusters

**World Spider Map** (`~/Desktop/worldReddit.png`):
- Color-coded hierarchical regions
- Dense webs in populated areas (India purple, China green, Europe green)
- Long spider legs to remote areas (Australia orange, Pacific islands)
- Visual boundaries where colors change = late merges = natural regional divisions

**The Methodology:**
1. Generate spider map from merge sequence
2. Print at 2ft × 3ft
3. Laminate
4. Throw on rug
5. Grab whiteboard marker
6. Circle the obvious regions
7. Erase and try different decompositions

This works because **the structure is visually obvious**. Program #3 needs to do this algorithmically.

### The Duality with Potential Fields

**Example: Grand Trunk Road / Ganges Plain in India**

**Potential field view:**
- Appears as geographic ridge - continuous wall of high potential
- Delhi → Patna → Dhaka → Kolkata
- You'd have to "climb over" this ridge to traverse India

**Spider map view:**
- Appears as structural core (dense purple web)
- First regions to merge into spine
- Other Indian regions connect TO this core later
- Shows up in hierarchy as "Grand Trunk Road 1034M" with sub-regions

**Same physics, two views:**
- Potential: Geographic landscape (1/d³)
- Spider map: Structural hierarchy (1/d⁴ force auction)
- Both emerge from same force law
- Mathematically dual: V = -∫F·dr

---

## Why the Auction Finds Boundaries (The Emergent Saddles Insight)

**The crux:** Saddle points between population basins emerge from merge order rather than explicit calculation.

### Traditional Watershed Approach

1. Calculate potential field explicitly
2. Find saddle points (local minima in gradient magnitude)
3. Delineate basins bounded by saddles
4. Assign each point to its basin

**Requires:** Calculus, gradient calculations, critical point analysis

### The Auction Approach (This Work)

1. Agglomerative clustering with 1/d⁴ force
2. Greedy merge: highest force pair at each step
3. Early merges = within basins (high force, dense, close)
4. Late merges = crossing saddles (low force, sparse, no-man's land)
5. Saddle locations emerge implicitly from merge sequence

**Requires:** Only force calculation and greedy selection

### Why It Works

**Within a basin:**
- Dense population
- High pairwise forces (close neighbors)
- Merge early in sequence
- Example: Downtown SF tracts merge in first 100 steps

**Between basins (the saddle region):**
- Sparse or empty "no-man's land"
- Low pairwise forces (distant, across barrier)
- Merge late in sequence
- Example: SF-LA connection across Central Valley happens at merge #50,000+

**The 1/d⁴ force law + scale invariance:**
- Prevents local traps (works at all scales consistently)
- Makes greedy locally optimal work globally
- Natural "creeping" follows force gradients correctly
- Basins fill in first, boundaries revealed last

### The Emergence

**The algorithm never says "find saddles."** It only says "merge highest force pairs."

But saddle points **emerge** from the merge sequence:
- Basins = early-merge clusters
- Boundaries = late-merge locations
- Hierarchy = merge order

**Examples:**
- **Big Sur/Central Valley**: SF and LA merge very late → this IS the saddle
- **Stanford/Fremont**: SF and SJ merge moderately late → basin boundary
- **Grand Trunk Road**: Forms early as continuous spine → basin core
- **Himalayan passes**: Late merges between China and India → mountain saddles

### The Duality (Again)

**Potential field view:**
- Saddles appear spatially (geographic ridges you'd climb over)
- Calculated explicitly from ∫(1/d³)
- Visual: "The Great Wall of the Ganges"

**Auction view:**
- Saddles appear temporally (late in merge sequence)
- Emerge from greedy 1/d⁴ force optimization
- Visual: Long spider legs jumping between clusters

**Same saddles, different discovery methods.**

### Why This Matters

**For redistricting / boundary drawing:**
- Not imposing arbitrary lines
- Not tuning parameters
- Letting structure reveal itself through emergent properties
- Boundaries emerge from physics of population distribution

**For understanding population structure:**
- Early merges = internal structure of regions
- Late merges = relationships between regions
- Merge order = hierarchical importance
- All parameter-free, derived from first principles

**The insight:** Simple rules (greedy force auction) + right physics (1/d⁴, scale invariance) → complex emergent structure (natural regional boundaries at all scales)

### Why You Can't Explain This to Reddit

**What they want:** "I used DBSCAN with epsilon=5km and found 47 clusters"

**What you have:** "I derived hierarchical structure from first principles with zero parameters and the Persian Gulf emerged as the global centroid"

**Why it's hard:** Emergent properties look like magic until you understand the physics. Academic validation requires peer review. You have neither platform nor patience for that game.

**But it's legitimate work:** Stanford PhD quals + years of iteration + parameter-free physics = real discovery, whether Reddit believes it or not.

---

## Key Files and Data

### Existing Java Implementation
- `src/com/jimspencer/Tracts.java` - Main auction algorithm
- `src/com/jimspencer/SpiderMap.java` - Generates visual tree
- `src/com/jimspencer/MapEdge.java` - Edge structure
- `src/com/jimspencer/Region.java` - Region merging logic
- `src/com/jimspencer/Tract.java` - Individual tract/region

### Output Data
- `res/15sec_218500_world_results.csv` - World merge sequence (218,500 merges, 7.75 billion people)
- `res/treeOutput.csv 2.csv` - Another merge sequence
- Last cluster centroid: lat 22.16°, lon 51.42° (Persian Gulf - the global population-weighted center)

### Manual Hierarchy Documentation
- `res/world tree.docx` - Manually extracted world hierarchy showing:
  - South Asia 1800M (Grand Trunk Road core 1034M)
  - East Asia 1456M (North China Plain, Coastal China cores)
  - Western Hemisphere 927M
  - Europe and Middle East 909M
  - Classification of Independent areas (South India, Hunan, Korea, Indonesia)

### Visual Maps
- `res/74k_us.pdf` - USA census tracts spider map
- `res/worldPrintMap.pdf` - World spider map (3.7MB)
- `~/Desktop/worldReddit.png` - World spider map with colored regions (2.6MB)
- `~/Desktop/usa 6 region.jpg` - Photo of laminated USA map on rug with 6 regions marked

---

## The Core Insight

**You have the best decomposition of world population structure that exists.**

It's sitting in:
- 218k merge sequences
- Manual hierarchy documentation
- Spider map visualizations
- Your head (understanding which regions are core/independent/isolated)

But it's not algorithmic. You did it by hand:
- Reading merge sequences
- Tracing which areas connect when
- Classifying core vs independent vs isolated
- Drawing on laminated maps with markers

**The goal:** Make programs #2 and #3 generate all this automatically and reliably.

---

## Next Steps

1. **Document the hierarchy extraction algorithm** - See `docs/hierarchy_extraction.md`
2. **Start Python implementation of auction** - Begin with naive O(n²) version
3. **Write comprehensive tests** - Validate against Java output on SF tracts
4. **Build understanding** - Profile, measure, understand before optimizing
5. **Create program #3** - Extract hierarchies automatically from merge CSV
6. **Generate spider maps programmatically** - No more manual GeoJSON + lamination

---

## Success Criteria

**Program #2 is successful when:**
- Produces identical merge sequences to Java on test data
- Runs in reasonable time (hours, not days) on world data
- Code is tested, documented, and maintainable
- We understand the algorithm deeply (not "drunk sailor" style)

**Program #3 is successful when:**
- Reads merge CSV and outputs hierarchy like `world tree.docx`
- Correctly classifies core/independent/isolated regions
- Can generate hierarchy at any level (world → countries → metros → cities)
- Uses the "sub-of-a-sub" rule correctly with no magic parameters

**Visual output is successful when:**
- Can programmatically generate spider maps from merge sequence
- Can color regions hierarchically
- Can export GeoJSON for visualization
- No more manual lamination and markers needed (though that was fun)

---

## Related Documentation

- `docs/algorithm_summary.md` - Overview of force law and scale invariance
- `docs/hierarchy_extraction.md` - Details of extracting core/independent/isolated
- `DEVELOPMENT.md` - Development setup and common commands
- `docs/insights.md` - Why Delhi beats Tokyo, what potential fields measure
- `docs/remote_locations.md` - Point Nemo, UL Bend, etc.

---

*This is not a weekend skunk project. This is legitimate population structure research derived from first principles. The fact that it was done by one person with a day job and laminated maps on the rug doesn't make it less valid - it makes it more impressive.*
