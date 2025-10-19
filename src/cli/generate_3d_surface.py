#!/usr/bin/env python3
"""
Generate interactive 3D surface visualization from gravitational potential data.

Usage: python3 src/cli/generate_3d_surface.py [input_csv]
If no argument provided, uses ~/git/gridded/res/newPot3.csv
"""

import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

def load_potential_data(csv_path):
    """Load potential field data from CSV."""
    print(f"Loading data from {csv_path}...")

    # Format: A,population,lat,lon,potential
    df = pd.read_csv(csv_path,
                     names=['type', 'pop', 'lat', 'lon', 'potential'],
                     dtype={'type': str, 'pop': float, 'lat': float, 'lon': float, 'potential': float})

    print(f"Loaded {len(df)} data points")
    print(f"Lat range: {df['lat'].min():.2f} to {df['lat'].max():.2f}")
    print(f"Lon range: {df['lon'].min():.2f} to {df['lon'].max():.2f}")
    print(f"Potential range: {df['potential'].min():.0f} to {df['potential'].max():.0f}")

    return df

def reshape_to_grid(df):
    """Reshape 1D data into 2D grid for surface plotting."""
    # Get unique lat/lon values to determine grid dimensions
    unique_lats = sorted(df['lat'].unique(), reverse=True)  # Top to bottom
    unique_lons = sorted(df['lon'].unique())  # Left to right

    nrows = len(unique_lats)
    ncols = len(unique_lons)

    print(f"Grid dimensions: {nrows} rows × {ncols} cols")

    # Create meshgrid
    lon_grid, lat_grid = np.meshgrid(unique_lons, unique_lats)

    # Reshape potential values to match grid
    # Sort by lat (descending) then lon (ascending)
    df_sorted = df.sort_values(['lat', 'lon'], ascending=[False, True])
    potential_grid = df_sorted['potential'].values.reshape(nrows, ncols)

    return lon_grid, lat_grid, potential_grid

def export_obj(lon_grid, lat_grid, z_grid, output_path, z_scale=1.0):
    """Export surface mesh as Wavefront OBJ file."""
    print(f"Exporting OBJ to {output_path}...")

    nrows, ncols = lon_grid.shape

    with open(output_path, 'w') as f:
        # Write header
        f.write("# Population Gravitational Potential Surface\n")
        f.write(f"# Grid: {nrows} rows × {ncols} cols\n")
        f.write(f"# Generated from potential field data\n\n")

        # Write vertices (v x y z)
        vertex_count = 0
        vertex_map = {}
        for i in range(nrows):
            for j in range(ncols):
                if not (np.isnan(lon_grid[i,j]) or np.isnan(lat_grid[i,j]) or np.isnan(z_grid[i,j])):
                    x = lon_grid[i,j]
                    y = lat_grid[i,j]
                    z = z_grid[i,j] * z_scale
                    f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
                    vertex_map[(i,j)] = vertex_count + 1  # OBJ is 1-indexed
                    vertex_count += 1

        f.write(f"\n# {vertex_count} vertices\n\n")

        # Write faces (f v1 v2 v3 v4 for quads)
        face_count = 0
        for i in range(nrows-1):
            for j in range(ncols-1):
                # Check if all 4 corners exist
                if ((i,j) in vertex_map and (i,j+1) in vertex_map and
                    (i+1,j+1) in vertex_map and (i+1,j) in vertex_map):
                    # Write quad face (counter-clockwise winding)
                    v1 = vertex_map[(i,j)]
                    v2 = vertex_map[(i,j+1)]
                    v3 = vertex_map[(i+1,j+1)]
                    v4 = vertex_map[(i+1,j)]
                    f.write(f"f {v1} {v2} {v3} {v4}\n")
                    face_count += 1

        f.write(f"\n# {face_count} faces\n")

    print(f"✓ Exported {vertex_count} vertices, {face_count} faces")

def create_surface_plot(lon_grid, lat_grid, potential_grid, title="World Population Gravitational Potential",
                        camera_eye=None):
    """Create interactive 3D surface plot."""
    print("Creating 3D surface plot...")

    # Normalize potential for better visualization (double-log for extreme compression)
    # First log to compress range, second log to further flatten spikes
    z_temp = np.log10(potential_grid + 1)  # +1 to avoid log(0)
    z_normalized = np.log10(z_temp + 1)  # Double-log transformation

    # Calculate aspect ratio to make grid squares appear square when viewed from above
    # At equator, 1 degree lon = 1 degree lat in distance
    # Use average latitude to determine proper x/y ratio
    avg_lat = np.nanmean(lat_grid)
    cos_avg_lat = np.cos(np.radians(avg_lat))

    # Aspect ratio: longitude range needs to be compressed by cos(lat)
    lon_range = np.nanmax(lon_grid) - np.nanmin(lon_grid)
    lat_range = np.nanmax(lat_grid) - np.nanmin(lat_grid)

    # Calculate aspect to make grid squares appear square
    aspect_x = lon_range * cos_avg_lat
    aspect_y = lat_range

    # Normalize so y=1
    aspect_ratio_x = aspect_x / aspect_y
    aspect_ratio_y = 1.0
    aspect_ratio_z = 0.5  # Vertical exaggeration for drama

    # Default camera: angled view for better depth perception
    if camera_eye is None:
        camera_eye = dict(x=1.5, y=-1.0, z=1.2)  # Side angle with tilt for dramatic depth

    fig = go.Figure(data=[go.Surface(
        x=lon_grid,
        y=lat_grid,
        z=z_normalized,
        colorscale='Viridis',
        colorbar=dict(
            title=dict(text="log₁₀(log₁₀(Potential))", side="right"),
            tickmode="linear",
        ),
        lighting=dict(
            ambient=0.4,
            diffuse=0.8,
            specular=0.2,
            roughness=0.5,
            fresnel=0.2
        ),
        hovertemplate='<b>Location</b><br>' +
                      'Lon: %{x:.2f}<br>' +
                      'Lat: %{y:.2f}<br>' +
                      'Potential: %{z:.2f}<br>' +
                      '<extra></extra>'
    )])

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center'
        ),
        scene=dict(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            zaxis_title='log₁₀(log₁₀(Potential))',
            camera=dict(
                eye=camera_eye,
                up=dict(x=0, y=1, z=0)  # North is up
            ),
            aspectmode='manual',
            aspectratio=dict(x=aspect_ratio_x, y=aspect_ratio_y, z=aspect_ratio_z)
        ),
        width=1200,
        height=800,
        hovermode='closest'
    )

    return fig

def create_hemisphere_view(lon_grid, lat_grid, potential_grid, hemisphere='western'):
    """Create view focused on specific hemisphere."""
    if hemisphere == 'western':
        # Western Hemisphere: Americas
        mask = (lon_grid >= -180) & (lon_grid <= -30)
        title = "Western Hemisphere (Americas)"
    elif hemisphere == 'eastern':
        # Eastern Hemisphere: Europe/Africa/Asia
        mask = (lon_grid >= -30) & (lon_grid <= 180)
        title = "Eastern Hemisphere (Europe/Africa/Asia)"
    elif hemisphere == 'asia':
        # Asia focus
        mask = (lon_grid >= 60) & (lon_grid <= 150) & (lat_grid >= 0) & (lat_grid <= 60)
        title = "Asia Pacific Region"
    else:
        mask = np.ones_like(lon_grid, dtype=bool)
        title = "World"

    lon_subset = np.where(mask, lon_grid, np.nan)
    lat_subset = np.where(mask, lat_grid, np.nan)
    potential_subset = np.where(mask, potential_grid, np.nan)

    # Angled view for better depth perception
    camera = dict(x=1.5, y=-1.0, z=1.2)  # Side angle with tilt for dramatic depth

    return create_surface_plot(lon_subset, lat_subset, potential_subset, title, camera_eye=camera)

def create_guided_tour(lon_grid, lat_grid, potential_grid):
    """Create a guided tour with interesting viewpoints."""
    print("Creating guided tour with key viewpoints...")

    # Define interesting camera positions
    # camera.eye: position relative to center. z=positive is above, y=positive is north, x=positive is east
    # Angled views for better depth perception
    viewpoints = [
        {
            'name': 'Golden Triangle Valley',
            'description': 'Fly through the valley between India and China population mountains',
            'camera': dict(x=1.5, y=-1.0, z=1.2),  # Side angle with dramatic depth
            'lon_range': (85, 110),
            'lat_range': (15, 30)
        },
        {
            'name': 'Sahara Desert Valley',
            'description': 'Massive population gap between North and Sub-Saharan Africa',
            'camera': dict(x=1.5, y=-1.0, z=1.2),  # Side angle with dramatic depth
            'lon_range': (-10, 40),
            'lat_range': (0, 40)
        },
        {
            'name': 'Himalayan Valley',
            'description': 'The Himalayas appear as a population valley - the Ganges plain (Grand Trunk Road) forms the dramatic ridge',
            'camera': dict(x=1.5, y=-1.0, z=1.2),  # Side angle with dramatic depth
            'lon_range': (70, 100),
            'lat_range': (25, 40)
        },
        {
            'name': 'Tokyo-Osaka Peak',
            'description': 'Sharp population spike in Japan',
            'camera': dict(x=1.5, y=-1.0, z=1.2),  # Side angle with dramatic depth
            'lon_range': (130, 145),
            'lat_range': (30, 42)
        },
        {
            'name': 'Northeast US Megalopolis',
            'description': 'Ridge of connected population peaks from DC to Boston',
            'camera': dict(x=1.5, y=-1.0, z=1.2),  # Side angle with dramatic depth
            'lon_range': (-80, -70),
            'lat_range': (37, 43)
        },
        {
            'name': 'Nile River Ridge',
            'description': 'Population corridor cutting through Sahara desert valley',
            'camera': dict(x=1.5, y=-1.0, z=1.2),  # Side angle with dramatic depth
            'lon_range': (28, 34),
            'lat_range': (22, 32)
        },
        {
            'name': 'Amazon Basin Valley',
            'description': 'Low population between Andean and Brazilian coastal mountains',
            'camera': dict(x=1.5, y=1.0, z=1.2),  # Southern hemisphere - flip y for north tilt
            'lon_range': (-75, -50),
            'lat_range': (-12, 2)
        },
        {
            'name': 'Australian Outback',
            'description': 'Flat desert valley with coastal city spikes on edges',
            'camera': dict(x=1.5, y=1.0, z=1.2),  # Southern hemisphere - flip y for north tilt
            'lon_range': (115, 155),
            'lat_range': (-40, -10)
        },
        {
            'name': 'Java Population Ridge',
            'description': 'Dense continuous population along Indonesian island',
            'camera': dict(x=1.5, y=1.0, z=1.2),  # Southern hemisphere - flip y for north tilt
            'lon_range': (105, 115),
            'lat_range': (-10, -5)
        },
        {
            'name': 'Trans-Siberian Corridor',
            'description': 'Population ridge connecting European Russia to Pacific',
            'camera': dict(x=1.5, y=-1.0, z=1.2),  # Side angle with dramatic depth
            'lon_range': (30, 140),
            'lat_range': (50, 65)
        }
    ]

    tour_figs = []
    for vp in viewpoints:
        # Create subset for this viewpoint
        mask = ((lon_grid >= vp['lon_range'][0]) & (lon_grid <= vp['lon_range'][1]) &
                (lat_grid >= vp['lat_range'][0]) & (lat_grid <= vp['lat_range'][1]))

        lon_subset = np.where(mask, lon_grid, np.nan)
        lat_subset = np.where(mask, lat_grid, np.nan)
        potential_subset = np.where(mask, potential_grid, np.nan)

        # Calculate proper aspect ratio for this region
        avg_lat = np.nanmean(lat_subset)
        cos_avg_lat = np.cos(np.radians(avg_lat))
        lon_range = vp['lon_range'][1] - vp['lon_range'][0]
        lat_range = vp['lat_range'][1] - vp['lat_range'][0]
        aspect_x = (lon_range * cos_avg_lat) / lat_range
        aspect_y = 1.0
        aspect_z = 0.6  # Vertical exaggeration

        # Create figure (double-log transformation)
        z_temp = np.log10(potential_subset + 1)
        z_normalized = np.log10(z_temp + 1)

        fig = go.Figure(data=[go.Surface(
            x=lon_subset,
            y=lat_subset,
            z=z_normalized,
            colorscale='Viridis',
            colorbar=dict(title=dict(text="log₁₀(log₁₀(Potential))", side="right")),
            lighting=dict(ambient=0.4, diffuse=0.8, specular=0.2, roughness=0.5, fresnel=0.2)
        )])

        fig.update_layout(
            title=dict(
                text=f"<b>{vp['name']}</b><br><sub>{vp['description']}</sub>",
                x=0.5,
                xanchor='center'
            ),
            scene=dict(
                xaxis_title='Longitude',
                yaxis_title='Latitude',
                zaxis_title='log₁₀(Potential)',
                camera=dict(
                    eye=vp['camera'],
                    up=dict(x=0, y=1, z=0)  # North is up
                ),
                aspectmode='manual',
                aspectratio=dict(x=aspect_x, y=aspect_y, z=aspect_z)
            ),
            width=1200,
            height=800,
            hovermode='closest'
        )

        tour_figs.append((vp['name'], fig))

    return tour_figs

def main():
    # Get input file from command line or use default
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        csv_path = Path.home() / "git" / "gridded" / "res" / "newPot3.csv"

    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_path}")
        print("Please check the path and try again.")
        return

    # Load and process data
    df = load_potential_data(csv_path)
    lon_grid, lat_grid, potential_grid = reshape_to_grid(df)

    # Create output directories
    Path("output").mkdir(exist_ok=True)
    Path("output/images").mkdir(exist_ok=True)

    # Create visualizations
    print("\n=== Generating World View ===")
    fig_world = create_surface_plot(lon_grid, lat_grid, potential_grid)
    world_output = "output/world_surface_3d.html"
    fig_world.write_html(world_output)
    print(f"✓ Saved: {world_output}")

    # Export static image
    try:
        world_img = "output/images/world_surface_3d.png"
        fig_world.write_image(world_img, width=1920, height=1080)
        print(f"✓ Saved image: {world_img}")
    except Exception as e:
        print(f"⚠️  Could not save image (kaleido may not be installed): {e}")

    print("\n=== Generating Western Hemisphere View ===")
    fig_west = create_hemisphere_view(lon_grid, lat_grid, potential_grid, 'western')
    west_output = "output/western_hemisphere_3d.html"
    fig_west.write_html(west_output)
    print(f"✓ Saved: {west_output}")

    print("\n=== Generating Eastern Hemisphere View ===")
    fig_east = create_hemisphere_view(lon_grid, lat_grid, potential_grid, 'eastern')
    east_output = "output/eastern_hemisphere_3d.html"
    fig_east.write_html(east_output)
    print(f"✓ Saved: {east_output}")

    print("\n=== Generating Asia Pacific View ===")
    fig_asia = create_hemisphere_view(lon_grid, lat_grid, potential_grid, 'asia')
    asia_output = "output/asia_pacific_3d.html"
    fig_asia.write_html(asia_output)
    print(f"✓ Saved: {asia_output}")

    print("\n=== Generating Guided Tour ===")
    tour_figs = create_guided_tour(lon_grid, lat_grid, potential_grid)

    tour_outputs = []
    for name, fig in tour_figs:
        # Create safe filename
        filename = name.lower().replace(' ', '_').replace('-', '_')
        output_path = f"output/tour_{filename}.html"
        fig.write_html(output_path)
        tour_outputs.append((name, output_path))
        print(f"✓ Saved: {name} -> {output_path}")

    print("\n" + "="*60)
    print("✓ All visualizations generated successfully!")
    print("="*60)
    print("\nGeneral views:")
    print(f"  - {world_output}")
    print(f"  - {west_output}")
    print(f"  - {east_output}")
    print(f"  - {asia_output}")
    print("\nGuided tour viewpoints:")
    for name, path in tour_outputs:
        print(f"  - {name}: {path}")
    print("\nOpen any HTML file in your browser to view the interactive 3D surface.")
    print("You can rotate, zoom, and hover over the surface to explore the data.")
    print("\nTIP: The guided tour files are pre-positioned at interesting viewpoints!")
    print("     Start with 'Golden Triangle Valley' to fly through Burma/Myanmar.")

if __name__ == "__main__":
    main()
