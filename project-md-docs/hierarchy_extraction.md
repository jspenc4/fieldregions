# Hierarchy Extraction Algorithm

## Purpose

Extract hierarchical structure from the merge sequence CSV produced by the auction algorithm (Tracts.java / program #2).

**Input:** Merge sequence CSV showing every merge from individual cells to global unity

**Output:** Hierarchical decomposition showing:
- Major regions at each level
- Classification of each region (core, independent, isolated)
- Population counts
- Geographic structure

## The Three Classifications

### Core Regions (First-Level Subs)

**Definition:** Major sub-regions that form the structural spine of the parent cluster.

**Identification:**
1. For a parent cluster, look at all merges that happened while it was forming
2. Sort child merges by population
3. Count children: 1, 2, 3, ...
4. **Stop when:** next child merged INTO one of the already-counted children
5. Those counted children are the cores

**Example from South Asia (1800M people):**
```
Grand Trunk Road 1034M - CORE (formed the spine)
  ├─ Mid Ganges 227M
  ├─ Bihar/Patna 97M
  ├─ Mouth of Ganges 177M (Dhaka, Calcutta)
  └─ Delhi Area 123M

Central India 259M - CORE
West Coast India 149M - CORE (Mumbai, Hyderabad)
```

These three cores merged together to form South Asia. They're the major structural components.

### Independent Areas

**Definition:** Regions that merged DURING the parent's formation but connected directly to the parent, not through one of the cores.

**Identification:**
- Merge timestamp falls within parent formation period
- Did NOT merge into one of the core regions
- Merged directly into the parent or one of its non-core parts

**Example from South Asia:**
```
South India 154M - INDEPENDENT
  ├─ Southern Tip India 68M
  └─ (other sub-regions)
```

South India merged while South Asia was forming, but it connected directly to the parent structure, not through the Grand Trunk Road core or other cores. It's a significant region but not part of the main spine.

### Isolated Areas

**Definition:** Regions that merged AFTER the parent's core structure was established.

**Identification:**
- Merge timestamp is late (after core formation complete)
- Small populations (stragglers)
- Often geographically remote (islands, Arctic regions)

**Example from World level:**
```
Final merges (#218,490-500):
- Arctic islands (lat 80+, pop 1-2)
- Pacific islands (Pitcairn, etc.)
- Remote Siberian cells
```

These are the last to connect because they're remote and/or tiny. They don't define regional structure.

---

## The "Sub-of-a-Sub" Rule

**Core principle:** The hierarchy is parameter-free. The structure tells you how many regions exist at each level.

**Algorithm:**

```python
def find_cores(parent_cluster, merge_sequence):
    """
    Find core sub-regions of a parent cluster.

    Returns list of core regions (no magic N parameter)
    """
    # Get all merges that happened during parent formation
    parent_start_merge = parent_cluster.first_merge_id
    parent_end_merge = parent_cluster.last_merge_id

    children = []
    for merge in merge_sequence[parent_start_merge:parent_end_merge]:
        if is_child_of(merge, parent_cluster):
            children.append(merge)

    # Sort by population (descending)
    children.sort(key=lambda x: x.population, reverse=True)

    cores = []
    for i, child in enumerate(children):
        # Check if this child merged into a previous core
        merged_into_core = False
        for core in cores:
            if child.merged_into(core):
                merged_into_core = True
                break

        if merged_into_core:
            # This is where we stop - child is "sub of a sub"
            break
        else:
            # This is a core region
            cores.append(child)

    return cores
```

**Key insight:** Stop when you hit a "sub of a sub" - when the next child merged into something you already counted. That means it's not a top-level structure, it's a subsidiary.

---

## Example: South Asia Decomposition

### From `res/world tree.docx`:

```
South Asia 1800M (tractId: 125509)

CORES (Major structural components):
1. Grand Trunk Road 1034M
   - Mid Ganges 227M
     └─ Bihar Patna Region 97M
   - Mouth of Ganges 177M
     ├─ Dhaka 90M
     └─ Calcutta 49M
   - Delhi Area 123M
     ├─ Delhi 92M
     └─ Punjab 88M

2. Central India 259M

3. West Coast India 149M
   ├─ Mumbai 58M
   └─ Hyderabad 62M

INDEPENDENT (Merged during formation, not part of cores):
- South India 154M
  └─ Southern Tip India 68M

(No isolated areas at this level - all regions are significant)
```

**Why Grand Trunk Road is the main core:**
- 1034M people (57% of South Asia)
- Formed first / has most early merges
- Other cores connect to this spine
- Geographically: Delhi → Patna → Dhaka → Calcutta corridor

**Why South India is independent:**
- Merged during South Asia formation
- But connected directly to parent, not through GTR core
- Significant population (154M) but structurally separate
- The Deccan Plateau is geographically distinct from Indo-Gangetic Plain

---

## Example: East Asia Decomposition

```
East Asia 1456M (tractId: 103360)

CORES:
1. North China Plain 301M
   ├─ Yellow River 150M
   │  └─ Zhengzhou Region 63M
   └─ North China 75M

2. South China 172M

3. Coastal China 124M

4. Japan 106M

5. Mountain China 105M

INDEPENDENT:
- Hunan 71M
- Korea 61M

(No isolated - all significant populations)
```

**The structure:** Multiple cores of similar size (~100-300M each). No single dominant spine like South Asia. This reflects East Asia's multipolar structure - several major population centers rather than one corridor.

---

## Example: World Level - Isolated Areas

```
Final merges in res/15sec_218500_world_results.csv:

Merge #218,481: 9 people at -23.875, -130.68 (Pacific island)
Merge #218,490: 1 person at 80.375, 47.875 (Arctic)
Merge #218,493: 1 person at 80.125, 57.875 (Arctic)
Merge #218,500: 1 person at 76.125, 152.875 (Arctic Siberia)
```

These are **isolated** - merged very late (after all major structure formed), tiny populations, geographically remote. They don't affect regional boundaries.

---

## Algorithm Implementation Strategy

### Phase 1: Parse Merge Sequence

```python
class Merge:
    merge_id: int          # Sequential merge number
    tract_i_id: int        # First region ID
    pop_i: float           # Population of first region
    lat_i: float, lon_i: float
    tract_j_id: int        # Second region ID
    pop_j: float           # Population of second region
    lat_j: float, lon_j: float

class Region:
    tract_id: int
    population: float
    first_merge: int       # When this region started forming
    last_merge: int        # When this region finished forming
    children: List[Region] # Sub-regions
    classification: str    # "core", "independent", "isolated"
```

### Phase 2: Build Merge Tree

```python
def build_merge_tree(merge_sequence):
    """
    Reconstruct the full merge tree from sequence.

    Returns root (global cluster containing all humanity)
    """
    regions = {}  # tract_id -> Region

    for merge in merge_sequence:
        # Create or get regions
        region_i = regions.get(merge.tract_i_id) or Region(merge.tract_i_id, merge.pop_i)
        region_j = regions.get(merge.tract_j_id) or Region(merge.tract_j_id, merge.pop_j)

        # Merge them
        parent = Region(
            tract_id=merge.tract_i_id,  # Parent takes ID of larger region
            population=region_i.population + region_j.population,
            first_merge=merge.merge_id,
            last_merge=merge.merge_id,
            children=[region_i, region_j]
        )

        regions[parent.tract_id] = parent

    # Last region is root (everyone)
    return parent
```

### Phase 3: Extract Hierarchy

```python
def extract_hierarchy(root, min_population=3_000_000):
    """
    Extract hierarchical structure from merge tree.

    Args:
        root: Root region (global or continental cluster)
        min_population: Stop recursing below this size

    Returns:
        Hierarchical structure with cores/independent/isolated
    """
    if root.population < min_population:
        return root

    # Find cores using sub-of-a-sub rule
    cores = find_cores(root)

    # Classify remaining children
    for child in root.children:
        if child in cores:
            child.classification = "core"
        elif merged_during_formation(child, root, cores):
            child.classification = "independent"
        else:
            child.classification = "isolated"

    # Recurse into cores and significant independent regions
    for child in cores + [c for c in root.children if c.classification == "independent"]:
        if child.population >= min_population:
            extract_hierarchy(child, min_population)

    return root
```

### Phase 4: Output Format

```python
def print_hierarchy(region, indent=0):
    """
    Print hierarchy in readable format like world tree.docx
    """
    prefix = "  " * indent
    classification = f" [{region.classification}]" if region.classification else ""
    print(f"{prefix}{region.name} {region.population/1e6:.0f}M{classification}")

    # Print cores first
    cores = [c for c in region.children if c.classification == "core"]
    for core in sorted(cores, key=lambda x: x.population, reverse=True):
        print_hierarchy(core, indent + 1)

    # Then independent
    independent = [c for c in region.children if c.classification == "independent"]
    if independent:
        print(f"{prefix}  Independent Areas:")
        for ind in sorted(independent, key=lambda x: x.population, reverse=True):
            print_hierarchy(ind, indent + 2)

    # Isolated not printed (too many, too small)
```

---

## Validation Strategy

### Test Against Manual Hierarchy

Compare program output against `res/world tree.docx`:

```python
def test_south_asia_cores():
    """Test that South Asia decomposition matches manual analysis"""
    root = load_merge_tree("res/15sec_218500_world_results.csv")
    south_asia = find_region(root, tract_id=125509)

    hierarchy = extract_hierarchy(south_asia)
    cores = [c for c in hierarchy.children if c.classification == "core"]

    # Should find 3 cores
    assert len(cores) == 3

    # Grand Trunk Road should be largest core
    assert cores[0].name == "Grand Trunk Road"
    assert cores[0].population == 1_034_000_000

    # Should find South India as independent
    independent = [c for c in hierarchy.children if c.classification == "independent"]
    assert any(c.name == "South India" for c in independent)
```

### Edge Cases to Handle

1. **Single-core regions**: Some parents have only one significant core (e.g., NYC metro might be single-core with suburbs as independent)

2. **Multiple cores of similar size**: East Asia has ~5 cores of 100-300M each. Algorithm should find all of them.

3. **Island regions**: Hawaii, New Zealand, etc. - clearly isolated, merged very late

4. **Continuous corridors**: Grand Trunk Road is one long core, not multiple separate regions

5. **Ambiguous boundaries**: When does Central Valley stop being "independent from Bay Area" and become "core of California"? The merge sequence tells you.

---

## Open Questions / Tuning Needed

### Minimum Population Threshold

**Question:** At what population do we stop recursing and displaying hierarchy?

**Current thinking:** 3 million (shows major metro areas, stops before getting too granular)

**Adjustable:** Could be parameter or could emerge from structure (stop when density of cores drops below threshold)

### Core vs Independent Threshold

**Question:** If a region merged "sort of late" in parent formation, is it independent or just a late core?

**Current thinking:** If it merged into an already-counted core, it's sub-of-a-sub (not a core). Otherwise, look at timing:
- Early in parent formation → Core
- Middle of formation → Independent
- Very late → Isolated

**Needs refinement:** Exact thresholds TBD, may vary by level of hierarchy

### Naming Regions

**Question:** How do we name regions automatically?

**Options:**
1. Use largest city name (Tract ID → lookup original lat/lon → geocode)
2. Use geographic descriptors (North China Plain, Grand Trunk Road)
3. Leave as Tract IDs and name manually

**For now:** Tract IDs with population counts. Naming can be manual post-processing.

---

## Success Criteria

Program #3 is successful when it can:

1. ✅ Read merge sequence CSV
2. ✅ Build complete merge tree
3. ✅ Identify cores using sub-of-a-sub rule
4. ✅ Classify independent vs isolated regions
5. ✅ Output hierarchy matching manual `world tree.docx`
6. ✅ Handle edge cases (single core, many cores, islands)
7. ✅ Recurse to desired depth (world → continent → country → metro)
8. ✅ Run in reasonable time (<1 minute for world hierarchy)

**Stretch goals:**
- Generate spider map GeoJSON with regions colored
- Export hierarchy in multiple formats (JSON, CSV, Markdown)
- Interactive visualization showing hierarchy at different levels
- Comparison mode: show how hierarchy changes with different force exponents

---

## Related Documentation

- `docs/spanning_tree_roadmap.md` - Overview of the three programs
- `docs/algorithm_summary.md` - The "sub-of-a-sub" rule and force law
- `res/world tree.docx` - Manual hierarchy (ground truth for validation)
- `DEVELOPMENT.md` - Setup and getting started

---

*The algorithm exists. It's documented in your head and in world tree.docx. Now we make it code.*
