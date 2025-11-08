# Visualization Parameters & Naming Convention

## Parameter Categories

### Algorithm Attributes (affect the calculated data)

1. **Exclusion radius** - Distance threshold for excluding nearby tracts from potential calculation
   - Current: 2 miles
   - Alternatives: 1 mile, 3 miles, adaptive (N nearest neighbors)
   - Rationale: Treats census tracts as extended area sources, not point masses

2. **Source data** - Input population dataset
   - Census tracts (~4,000 people, ~1-5km spacing)
   - Block groups (~1,000 people, ~0.5km spacing)
   - Blocks (~100 people, ~0.1km spacing in cities)
   - World GPW grid (15 arc-minute, ~28km at equator)

3. **Potential formula** - Which force law to integrate
   - `1/d³` - from 1/d⁴ force (social cohesion, current default)
   - `1/d` - from 1/d² force (gravity analog)
   - `1/d²` - from 1/d³ force (intermediate)

4. **Sampling strategy** - Where to evaluate potential
   - Triangle centers (current default, follows data density)
   - Regular grid (uniform spacing)
   - Census tract points (creates singularities without exclusion)

5. **Geographic bounds** - Regional subset
   - USA (72,539 tracts)
   - California (8,836 tracts)
   - SF Bay Area (1,260 tracts)
   - Custom region (any CSV with lon, lat, pop)

6. **Latitude correction** - How to handle spherical Earth
   - cos(avg_lat) - current simple approach
   - cos(local_lat) - more precise per-point correction
   - Haversine distance - full great-circle calculation

### Visualization Attributes (affect the presentation)

1. **Colors** - Colormap for rendering
   - Grayscale/Greys (current default for 3D printing)
   - Viridis, Plasma, Inferno (perceptually uniform)
   - Custom monochrome (single hue with varying lightness)

2. **Mesh vs surface** - Rendering approach
   - Triangle mesh (go.Mesh3d) - preserves data structure, shows triangulation
   - Interpolated surface (go.Surface) - smooth, regular grid via griddata
   - Point cloud (go.Scatter3d) - raw sample points

3. **Z aspect ratio** - Height scaling relative to width
   - 8% (current default: 2cm / 25cm for printing)
   - Scientific (1:1 aspect after lat/lon correction)
   - Exaggerated (15-20% for dramatic effect)

4. **Output format** - File type and use case
   - HTML (Plotly interactive) - exploration and presentation
   - STL (binary mesh) - 3D printing
   - OBJ (text mesh) - Blender import, rendering
   - PNG (screenshot) - documentation, sharing

5. **Camera angle** - Initial view position
   - Overhead (top-down, eye.z large)
   - Angled (eye = 1.5, 1.5, 1.2) - current default
   - "Looking north" (low eye.y, moderate eye.z)
   - Custom (user-specified eye position)

6. **Lighting** - Illumination model (for mesh/surface)
   - Default: ambient=0.5, diffuse=0.8, specular=0.2
   - High contrast: ambient=0.3, diffuse=0.9, specular=0.5
   - Flat: ambient=0.9, diffuse=0.5, specular=0.0

7. **Grid resolution** (surface interpolation only)
   - 300×200 (current default)
   - 500×333 (higher detail)
   - 150×100 (faster preview)

## Proposed Naming Convention

### Directory Structure
```
output/
├── {region}/
│   ├── {region}_{formula}_{sampling}_{exclusion}.csv     # Calculated data
│   ├── {region}_{formula}_{exclusion}_{render}_{format}  # Visualizations
│   └── metadata.json                                      # Parameter record
```

### File Naming Pattern

**Calculated potential data:**
`{region}_{formula}_{sampling}_{exclusion}.csv`

Examples:
- `usa_d3_triangles_2mile.csv`
- `california_d1_triangles_none.csv`
- `sf_bay_d3_grid_adaptive.csv`

**Visualizations:**
`{region}_{formula}_{exclusion}_{render}_{zaspect}.{format}`

Examples:
- `usa_d3_2mile_mesh_8pct.html`
- `california_d3_2mile_surface_8pct.stl`
- `sf_bay_d1_none_mesh_scientific.obj`

**Screenshots/exports:**
`{region}_{formula}_{exclusion}_{render}_{view}.png`

Examples:
- `usa_d3_2mile_surface_overhead.png`
- `california_d3_2mile_mesh_north.png`

### Metadata JSON
Each calculation should generate a metadata file recording all parameters:

```json
{
  "region": "usa",
  "source_data": "res/censusTracts.csv",
  "source_type": "census_tracts",
  "num_tracts": 72539,
  "potential_formula": "1/d^3",
  "force_law": "1/d^4",
  "exclusion_radius_miles": 2.0,
  "sampling_strategy": "triangle_centers",
  "num_samples": 145050,
  "latitude_correction": "cos_avg_lat",
  "calculated_at": "2025-10-15T21:10:00",
  "potential_range": [1.23e4, 4.56e6],
  "variation_ratio": 40.2,
  "script_version": "02_calculate_potential_d3_exclude_radius.py"
}
```

## Current Defaults (October 2024)

**Algorithm:**
- Exclusion: 2 miles
- Source: Census tracts
- Formula: 1/d³ (from 1/d⁴ force)
- Sampling: Triangle centers
- Lat correction: cos(avg_lat)

**Visualization:**
- Colors: Grayscale
- Render: Both mesh and surface
- Z aspect: 8% (20mm / 250mm)
- Format: HTML (interactive)
- Camera: Angled (1.5, 1.5, 1.2)
- Lighting: ambient=0.5, diffuse=0.8, specular=0.2

## Migration Path

Current files to rename:
- `triangle_centers_d3_potential_2mile.csv` → `{region}_d3_triangles_2mile.csv`
- `preview_mesh_2mile.html` → `{region}_d3_2mile_mesh_8pct.html`
- `preview_surface_2mile.html` → `{region}_d3_2mile_surface_8pct.html`

Or keep current names and adopt convention going forward - avoid breaking existing references.
