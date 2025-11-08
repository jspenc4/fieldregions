# World's Most Remote Locations

Analysis using population potential with 30-mile hexagonal grid (world_gpw_hex30mi_30mile).

## Global Ranking by Remoteness

### 1. Southern Ocean (Point Nemo Region)
- **Location**: 48.1°S, 141.4°W
- **Potential**: 0.0166 (absolute minimum)
- **Note**: Point Nemo itself (~48.9°S, 123.4°W) has potential 0.0183

The most remote point on Earth's surface. When astronauts on the ISS pass overhead, they are closer to other humans than anyone on Earth.

### 2. Australian Outback
- **Location**: 29.9°S, 128.9°E
- **Population**: 1 person
- **Potential**: 0.11
- **Comparison**: 7× more accessible than Point Nemo

Central/Western Australia desert. Surprisingly more remote than Arctic Siberia.

### 3. Arctic Siberia
- **Location**: 74.1°N, 136.1°E
- **Population**: 3 people
- **Potential**: 0.16
- **Comparison**: 10× more accessible than Point Nemo

New Siberian Islands/Arctic coast region.

### 4. Amazon Rainforest
- **Location**: 1.6°N, 56.9°W
- **Population**: 12 people
- **Potential**: 0.47
- **Comparison**: 28× more accessible than Point Nemo

Deep Amazon in Brazil/Guyana border region. Rivers provide transportation, making it less isolated than deserts.

### 5. Sahara Desert
- **Location**: 23.1°N, 9.6°W
- **Population**: 21 people
- **Potential**: 0.71
- **Comparison**: 43× more accessible than Point Nemo

Northern Mali/Mauritania.

## Continental United States (CONUS)

### Most Remote Location: UL Bend Wilderness, Montana
- **Location**: 47.6°N, 107.6°W
- **Population**: 20 people
- **Potential**: 0.89
- **Note**: Part of Charles M. Russell National Wildlife Refuge

**Key Insight**: The most remote spot in the continental US (0.89) is actually **less remote** than the Sahara Desert (0.71). The US has no truly isolated areas by global standards.

## Peak for Comparison

### New Delhi, India
- **Location**: 28.6°N, 77.1°E
- **Potential**: 7,593
- **Comparison**:
  - 415,000× more accessible than Point Nemo
  - 67,000× more accessible than Australian Outback
  - 8,500× more accessible than UL Bend Wilderness

## Why 1/d⁴ Force Law?

The force law captures human behavior: **if something is twice as close, you're 16× more likely to go there.**

This steep distance decay reflects reality:
- Grocery store 1 mile away vs 2 miles? You'll visit the closer one far more than 2× as often
- Job 10 miles vs 20 miles? The closer one is WAY more attractive
- Friend 5 minutes vs 20 minutes away? You'll see the nearby friend much more frequently

### Physical Analogy: Radar
Radar signals also follow 1/d⁴:
- Signal travels to target: loses 1/d²
- Signal reflects back: loses another 1/d²
- Total: 1/d⁴

### Scale Invariance
The 1/d⁴ force law has a special property:
- Grid with 1 person per cell: neighbors interact with (1×1)/1⁴ = 1
- Coarsen to 4 people per cell, 2 units apart: (4×4)/2⁴ = 16/16 = 1
- **Same force, different resolution**

This ensures results are independent of data granularity.

### Force vs Potential
- **Force law** (pairwise interaction): 1/d⁴
- **Potential** (cumulative field): 1/d³ (integral of force)

---

*Analysis generated 2025-01-25*
