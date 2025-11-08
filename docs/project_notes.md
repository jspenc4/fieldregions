# Population Clustering Project - Key Insights

## Algorithm Overview
- **Distance⁴ clustering**: Mutual attraction = (pop₁ × pop₂) / distance⁴
- **Resolution-independent**: Works at any grid size (15 arc-minute, 1km, etc.)
- **Parameter-free**: No magic numbers, thresholds, or tunable parameters
- **218,330 merge events** from ~200K+ populated cells → 1 global cluster

## Final Result
- Cluster 125509 (started at 25.625°N, 85.125°E - Bihar, India)
- Final population: 7,757,980,470 (≈7.76B)
- Final centroid: **22.16°N, 51.43°E** (Persian Gulf/Eastern Saudi Arabia)
  - This is the population-weighted gravitational center of Afro-Eurasia

## Hierarchical Decomposition - "Sub-of-a-Sub" Rule

**The elegant part:** Completely parameter-free hierarchy determination.

### Algorithm:
1. For any parent cluster P, sort children by population (largest first)
2. Count children: 1, 2, 3, ...
3. **Stop when:** next child merged into one of the already-counted children
4. Those are the "major regions" of P
5. Recurse into each major region

### Example (USA):
- Top 5 regions emerge naturally (Northeast, Southeast, Midwest, Southwest, West)
- 6th largest (Chicago) merged into Midwest → it's a sub-of-a-sub, not a primary region
- No magic "top N" parameter - the structure determines N

### Why This Matters:
- Works at every scale (neighborhoods → cities → regions → continents)
- No arbitrary cutoffs
- Hierarchy emerges purely from merge sequence

## Visualization Challenges

### Current Problem:
- Map shows all 218K merges as colored lines
- Looks like "population density with pretty colors"
- Hierarchical structure is buried in visual noise
- "Vector but looks raster"

### Solutions to Explore:

#### 1. **3D Potential Field Globe** ⭐ (Priority)
- Calculate 1/d³ potential at every point: `Σ (population_i / distance_i³)`
- Population centers = deep valleys
- Barriers (Himalayas, Sahara, oceans) = ridges
- Saddle points = natural crossing points between regions
- Interactive 3D globe (Three.js)
- **Nobody else has this**

#### 2. **Interactive Tree Explorer**
- Click to expand/collapse regions
- Shows sub-of-a-sub hierarchy visually
- Auto-generated region names based on geography + scale
- Linked to map view

#### 3. **Selective Network Visualization**
- Show only major merges (not all 218K)
- Highlight key transition points
- Animate by merge sequence

#### 4. **Hierarchical Edge Bundling**
- Tree structure explicit in layout
- Shows structure, not just density

## What Already Exists (Oct 2024)

### ✅ 3D Potential Field Visualizations (COMPLETED)
**Location:** `/Users/jim-spencer/git/javaMap/output/`

You already built interactive 3D potential field visualizations using Plotly:
- World surface (59 MB interactive HTML)
- Western hemisphere (53 MB)
- Eastern hemisphere (47 MB)
- Asia Pacific (41 MB)
- **10 guided tour viewpoints** with dramatic camera angles:
  - Golden Triangle Valley (Burma between India/China)
  - Sahara Desert Valley
  - Himalayan Valley
  - Amazon Basin Valley
  - Australian Outback
  - Java Population Ridge
  - Nile River Ridge
  - Northeast US Megalopolis
  - Tokyo-Osaka Peak
  - Trans-Siberian Corridor

**Current implementation:** Uses **1/d³ potential** (population / distance³)
**Location:** `/Users/jim-spencer/git/gridded/src/com/jimspencer/Main.java`

**Physical interpretation:** 1/d³ potential derived from 1/d⁴ clustering force:
- Force: F = (pop₁ × pop₂) / distance⁴
- Potential: ∫F·dr → Σ(population / distance³)
- Shows "energy cost" to traverse terrain
- Saddle points = natural regional boundaries

**Implementation** (Line 106 in Main.java):
```java
// Current (1/d³):
double d = distance(lat, lon, pp.lat, pp.lon);
newPoint.potential += pp.pop / (d * d * d);
```

Then regenerate `newPot3.csv` and re-run `generate_3d_surface.py`.

### ✅ Manual Hierarchical Tree (COMPLETED)
**Location:** `/Users/jim-spencer/Google Drive/My Drive/javaMap/res/worldtree.txt`

626 lines of manually-labeled hierarchical breakdown using the sub-of-a-sub rule:
- 8 top-level regions (South Asia 1.8B → Isolated areas)
- Recursive breakdown to 3M population clusters
- Geographic and political naming conventions established
- This serves as the **Rosetta Stone** for auto-naming algorithm

**Example structure:**
```
1. South Asia 1800M
  1.1 Grand Trunk Road 1039M
    1.1.1 Mid Ganges 227M
      1.1.1.1 Bihar 111M
        1.1.1.1.1 Patna 97M
```

## Technical Next Steps

### 1. Update to d³ Potential Field ⚠️ HIGH PRIORITY
- Modify `/Users/jim-spencer/Google Drive/My Drive/gridded/src/com/jimspencer/Main.java` line 91
- Regenerate `newPot3.csv` with 1/d³ calculation
- Re-run `generate_3d_surface.py` to create new visualizations
- Compare 1/d vs 1/d³ to see how barriers appear more prominent

### 2. Tree Construction Algorithm (Foundation)
```javascript
// Parse CSV → build tree structure
// Each node: {id, children[], parent, population, centroid, mergeOrder}
// Implement sub-of-a-sub detection (stops when next child is descendant of previous)
```

**Input:** `/Users/jim-spencer/git/javaMap/res/15sec_218500_world_results.csv` (25 MB, 218K merges)
**Reference:** Manual tree in `worldtree.txt` shows expected structure

### 3. Auto-Naming System
- Reverse geocoding for coordinates
- Scale-based naming (use worldtree.txt as training data):
  - <10M: City names (Patna, Tokyo, Lagos)
  - 10M-100M: Metropolitan regions / corridors (Grand Trunk Road, Rhine-Ruhr)
  - 100M-1B: Countries/major regions (South Asia, East Africa)
  - >1B: Continental names
- Handle multi-country clusters (Grand Trunk Road spans Pakistan/India/Bangladesh)
- Distinguish "Independent" (late merge, significant size) vs "Isolated" (very late, small)

### 4. Interactive Tree Explorer
- Click to expand/collapse regions
- Show population, centroid, merge order for each node
- Highlight on map when node selected
- Color code by merge timing (early = blue, late = red)
- Export as standalone HTML with embedded data

### 5. Physical 3D Print
- Western hemisphere test print coming soon
- Shows physical topography of human gravitational field

## Applications Beyond Population

The algorithm is domain-agnostic. Could apply to:
- Stellar masses / galaxy clusters
- Economic centers (GDP + trade distance)
- Neural network analysis
- Disease spread modeling
- Social network clustering

Key requirements:
1. Weighted points in space
2. Meaningful distance metric
3. Natural hierarchical structure to discover

## Project History
- Algorithm developed years ago
- Held back due to fear of trolls
- Posted to r/dataisbeautiful (Oct 2024)
  - 14K views, 0 net upvotes
  - Comments: "ugly colors", "repellently ugly", sarcastic "masterpiece"
- Deleted Reddit account to avoid obsessive checking
- Resolution: Build the visualizations that make the insight undeniable

## File Locations
- Merge data: (need to identify CSV location)
- Manual hierarchical breakdown: `/Users/jim-spencer/Google Drive/My Drive/javaMap/res/worldtree.txt`
- Visualization: `/Users/jim-spencer/git/javaMap/res/worldPrintMap.png`
- GeoJSON: `/Users/jim-spencer/Google Drive/My Drive/javaMap/res/world 15 sec try 2.json`

## Key Insight
The Persian Gulf centroid isn't programmed in - it **emerges** from first principles. It's where ancient trade routes converged because it's the actual gravitational center of human civilization accounting for population mass and geographic distance.

---

*"No magic numbers. Who do you think I am?"*
