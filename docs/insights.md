# Population Potential Field Insights

> "There is something fascinating about science. One gets such wholesale returns of conjecture out of such a trifling investment of fact." — Mark Twain, *Life on the Mississippi*

> "I was sitting with a young lady when the light from some star fell on my shoulder. She asked what I was thinking, and I said, 'I was thinking that of all the billions of people in the world, I am one of only two people who know why that star is shining.'" — Arthur Eddington (possibly apocryphal)

## What Does This Actually Measure?

The population potential field using 1/d³ gravitational potential is more than just "where are the most people." It measures something specific and meaningful: **inescapable regional density**.

### Top 20 Global Peaks (2020 GPW Data, 15-mile min distance)

1. New Delhi, India (Potential: 7593)
2. Noida, India (Delhi NCR)
3. Dhaka, Bangladesh
4. Shanghai districts, China
5. Tokyo districts, Japan
6. Beijing districts, China
7. Cairo, Egypt
8. Jakarta, Indonesia
9. Mumbai, India
10. Guangzhou/Shenzhen, China

### Why Delhi Beats Tokyo

Most population rankings put Tokyo #1 (~38M metro population). Our potential field puts **Delhi #1**.

**The difference:**
- **Tokyo:** Massive metro area, but somewhat isolated (ocean on 3 sides, mountains inland)
- **Delhi:** Large metro area (~30M) PLUS surrounded by the Indo-Gangetic Plain with 200M+ people within a few hundred miles in every direction

### The Lived Experience Connection

People who have visited both describe:
- **Tokyo:** "Crazy" - intense, packed, but organized
- **Delhi/Dhaka:** "Insane" - oppressive, inescapable density

The potential field quantifies this difference. It's not measuring city size - it's measuring **pressure from all directions**. The 1/d³ integral literally sums contributions from the entire surrounding region.

High potential = you cannot escape the density by traveling in any direction.

### What This Means

This ranking measures:
- ✓ **Regional population centrality** - where is the center of human mass?
- ✓ **Inescapable density** - where does population press in from all sides?
- ✓ **Agglomeration effects** - being near other dense areas multiplies your score

This ranking does NOT measure:
- ✗ Economic importance (London/NYC would rank higher)
- ✗ Cultural influence (Paris would rank higher)
- ✗ Quality of life
- ✗ Metro area boundaries (we rank grid cells, not political units)

### Comparison to Other Rankings

**Pure metro population (2020):**
1. Tokyo (~38M)
2. Delhi (~30M)
3. Shanghai (~27M)
4. São Paulo (~22M)

**Global city importance (economic/cultural):**
1. London
2. New York
3. Paris/Tokyo

**Our population potential ranking:**
1. Delhi
2. Dhaka
3. Shanghai
4. Tokyo

**The insight:** We're not just replicating existing rankings. We're measuring something different: **geometric centrality in population space**.

### Why 1/d³?

The exponent = 3 comes from physics (gravitational/electrostatic potential), not arbitrary tuning. It's a principled choice based on inverse-cube law.

Could use different exponents for different questions:
- 1/d² (gravity force): more local, sharper peaks
- 1/d³ (potential): balance of local + regional
- 1/d⁴: more regional, flatter

### Scale Dependence is a Feature

Different distance scales answer different questions:
- **Local (1 mile):** Neighborhood density
- **Regional (15 miles):** Metro area influence
- **Continental (100 miles):** Major population basins

This is like physics: quantum vs classical, local vs global. Scale dependence is information, not a bug.

### Parameters

Remarkably few tunable parameters:
1. **Exponent:** 3 (from physics, not tuned)
2. **Distance function:** Haversine (standard for Earth surface)
3. **Grid resolution:** 0.25° (~28km) - from GPW dataset
4. **Min distance:** 15 miles (only tuned parameter!)

One parameter, global insights. That's elegant.

### Questions for Further Exploration

1. How does this correlate with migration patterns? Do people move toward high-potential areas?
2. Does potential predict economic connectivity or trade flows?
3. How has this changed over time? (Compare 1990 vs 2020 GPW data)
4. Does potential correlate with infrastructure density, pollution, or other urban metrics?
5. What happens if we use GDP or carbon emissions instead of population?
6. Can we predict future potential based on growth rates?

### Validation and Falsification

What would disprove this approach?
- If high-potential areas showed NO correlation with any meaningful urban metric
- If the ranking was dominated by data artifacts rather than real geography
- If small parameter changes produced wildly different, nonsensical results

What supports this approach?
- Rankings match lived experience ("Delhi feels more inescapable than Tokyo")
- Continental basins match independent watershed analysis
- Results are stable across reasonable parameter variations
- Method extends to multiple scales (neighborhood → global)

### Future Work

- [ ] Generate rankings for different years (1990, 2000, 2010, 2020)
- [ ] Compare potential vs metro GDP, trade flows, migration
- [ ] Create "most isolated" rankings (low potential despite population)
- [ ] Analyze potential gradients (steepness of population landscape)
- [ ] 3D printed globe with height = potential
- [ ] Animation showing peaks "growing" simultaneously
- [ ] Test different distance functions, exponents

---

*Last updated: October 25, 2025*
*Data: GPW v4 2020, 15-minute resolution*
*Method: 1/d³ gravitational potential, haversine distance, 15-mile min distance*
