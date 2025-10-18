#!/usr/bin/env python3
"""
Generate PNG images from potential data with multiple camera angles and render styles.
"""

import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Delaunay
from scipy.interpolate import griddata
from pathlib import Path
import sys

def load_potential_data(csv_path):
    """Load triangle centers + potential from CSV."""
    data = np.loadtxt(csv_path, delimiter=',')
    lons = data[:, 0]
    lats = data[:, 1]
    potentials = data[:, 2]
    return lons, lats, potentials

def create_mesh_figure(lons, lats, potentials, title, camera, lighting, z_transform=None, color_transform=None, colorscale='Greys'):
    """Create a Mesh3d figure."""
    tri = Delaunay(np.column_stack((lons, lats)))

    # Apply Z transformation (for height)
    p_shifted = potentials - potentials.min()
    if z_transform is not None:
        p_transformed = z_transform(p_shifted)
    else:
        p_transformed = p_shifted

    # Scale Z to 8% of longitude range
    lon_range = lons.max() - lons.min()
    z_normalized = p_transformed / p_transformed.max()
    z_scaled = z_normalized * (lon_range * 0.08)

    # Apply color transformation (for intensity/color mapping)
    if color_transform is not None:
        color_values = color_transform(p_shifted)
    else:
        color_values = p_shifted

    # Normalize color values for colorscale
    color_normalized = color_values / color_values.max()

    fig = go.Figure(data=[go.Mesh3d(
        x=lons,
        y=lats,
        z=z_scaled,
        i=tri.simplices[:, 0],
        j=tri.simplices[:, 1],
        k=tri.simplices[:, 2],
        intensity=color_normalized,
        colorscale=colorscale,
        showscale=False,
        lighting=lighting,
        flatshading=False,
        hoverinfo='skip'
    )])

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis=dict(title='Longitude (°)', showgrid=True, visible=True),
            yaxis=dict(title='Latitude (°)', showgrid=True, visible=True),
            zaxis=dict(title='', showgrid=False, visible=False),
            aspectmode='data',
            camera=camera,
            bgcolor='white'
        ),
        width=1920,
        height=1080,
        showlegend=False,
        paper_bgcolor='white',
        margin=dict(l=0, r=0, t=40, b=0)
    )

    return fig

def create_surface_figure(lons, lats, potentials, title, camera, lighting, z_transform=None, grid_res=(300, 200)):
    """Create a Surface figure."""
    # Interpolate to regular grid
    grid_lon = np.linspace(lons.min(), lons.max(), grid_res[0])
    grid_lat = np.linspace(lats.min(), lats.max(), grid_res[1])
    lon_mesh, lat_mesh = np.meshgrid(grid_lon, grid_lat)

    pot_mesh = griddata(
        np.column_stack((lons, lats)),
        potentials,
        (lon_mesh, lat_mesh),
        method='linear'
    )
    pot_mesh = np.nan_to_num(pot_mesh, nan=potentials.min())

    # Apply Z transformation
    p_shifted = pot_mesh - potentials.min()
    if z_transform is not None:
        p_transformed = z_transform(p_shifted)
    else:
        p_transformed = p_shifted

    # Scale Z to 8% of longitude range
    lon_range = lons.max() - lons.min()
    z_normalized = p_transformed / p_transformed.max()
    z_mesh = z_normalized * (lon_range * 0.08)

    fig = go.Figure(data=[go.Surface(
        x=lon_mesh,
        y=lat_mesh,
        z=z_mesh,
        colorscale='Greys',
        showscale=False,
        lighting=lighting,
        hoverinfo='skip'
    )])

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis=dict(title='Longitude (°)', showgrid=True, visible=True),
            yaxis=dict(title='Latitude (°)', showgrid=True, visible=True),
            zaxis=dict(title='', showgrid=False, visible=False),
            aspectmode='data',
            camera=camera,
            bgcolor='white'
        ),
        width=1920,
        height=1080,
        showlegend=False,
        paper_bgcolor='white',
        margin=dict(l=0, r=0, t=40, b=0)
    )

    return fig

def main():
    # Parse arguments
    quick_mode = True  # Default to quick mode
    z_scaling = 'sqrt'  # Default to sqrt scaling
    region = None

    for arg in sys.argv[1:]:
        if arg == '--full':
            quick_mode = False
        elif arg.startswith('--scaling='):
            z_scaling = arg.split('=')[1]
        elif not arg.startswith('-'):
            region = arg

    if region is None:
        print("Usage: python3 export_images.py <region> [--full] [--scaling=linear|sqrt|log]")
        print("Example: python3 export_images.py sf_bay")
        print("         python3 export_images.py california --full")
        print("         python3 export_images.py usa_grid_5mi --scaling=sqrt")
        print("")
        print("Default: quick mode (best angles + dramatic lighting + sqrt scaling)")
        print("  --full: generate all angle/lighting combinations")
        print("  --scaling: linear (dramatic peaks), sqrt (balanced), log (max detail)")
        sys.exit(1)

    # Load data
    csv_path = f'output/{region}/triangle_centers_d3_potential_2mile.csv'
    print(f"Loading {csv_path}...")
    lons, lats, potentials = load_potential_data(csv_path)
    print(f"Loaded {len(lons):,} sample points")

    # Camera angles - all available
    all_cameras = {
        'overhead': dict(eye=dict(x=0, y=0, z=2.5)),
        'angled': dict(eye=dict(x=1.5, y=1.5, z=1.2)),
        'north': dict(eye=dict(x=0, y=-2.0, z=0.8)),
        'south': dict(eye=dict(x=0, y=2.0, z=0.8)),
        'east': dict(eye=dict(x=2.0, y=0, z=0.8)),
        'west': dict(eye=dict(x=-2.0, y=0, z=0.8)),
        'low': dict(eye=dict(x=2.0, y=2.0, z=0.5)),
    }

    # Quick mode: best angles only (cardinal/diagonal directions)
    quick_cameras = {
        'north': dict(eye=dict(x=0, y=-2.0, z=0.8)),        # Looking from south
        'northeast': dict(eye=dict(x=1.4, y=-1.4, z=0.8)),  # Looking from southwest
        'northwest': dict(eye=dict(x=-1.4, y=-1.4, z=0.8)), # Looking from southeast
        'low_se': dict(eye=dict(x=2.0, y=2.0, z=0.5)),      # Low angle from southeast
    }

    # Lighting presets - all available
    all_lightings = {
        'default': dict(ambient=0.5, diffuse=0.8, specular=0.2),
        'dramatic': dict(ambient=0.3, diffuse=0.9, specular=0.5),
        'flat': dict(ambient=0.9, diffuse=0.5, specular=0.0),
    }

    # Quick mode: dramatic lighting only
    quick_lightings = {
        'dramatic': dict(ambient=0.3, diffuse=0.9, specular=0.5),
    }

    # Z scaling transforms
    z_transforms = {
        'linear': None,  # No transformation
        'sqrt': lambda p: np.sqrt(p),
        'log': lambda p: np.log10(p + 1),
    }

    if z_scaling not in z_transforms:
        print(f"Error: Invalid scaling '{z_scaling}'. Must be one of: {list(z_transforms.keys())}")
        sys.exit(1)

    z_transform = z_transforms[z_scaling]

    # Select mode
    cameras = all_cameras if not quick_mode else quick_cameras
    lightings = all_lightings if not quick_mode else quick_lightings

    mode_str = "FULL" if not quick_mode else "QUICK"
    print(f"Mode: {mode_str}")
    print(f"Z Scaling: {z_scaling}")
    print(f"Cameras: {list(cameras.keys())}")
    print(f"Lightings: {list(lightings.keys())}")
    print(f"Will generate: {len(cameras) * len(lightings) * 2} images\n")

    # Output directory
    output_dir = Path(f'output/{region}/renders')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate images
    render_types = ['mesh', 'surface']

    for render_type in render_types:
        for cam_name, camera in cameras.items():
            for light_name, lighting in lightings.items():
                title = f"{region.title().replace('_', ' ')} - {render_type.title()} - {cam_name}/{light_name} - {z_scaling}"
                filename = f"{region}_d3_2mile_{render_type}_{cam_name}_{light_name}_{z_scaling}.png"
                output_path = output_dir / filename

                print(f"Generating {filename}...")

                if render_type == 'mesh':
                    fig = create_mesh_figure(lons, lats, potentials, title, camera, lighting, z_transform)
                else:
                    fig = create_surface_figure(lons, lats, potentials, title, camera, lighting, z_transform)

                fig.write_image(str(output_path))
                print(f"  Saved to {output_path}")

    print(f"\nDone! Generated {len(cameras) * len(lightings) * len(render_types)} images")
    print(f"Open with: open {output_dir}")

if __name__ == '__main__':
    main()
