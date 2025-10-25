"""
Visualization utilities for population potential fields.

Provides functions to create interactive 3D visualizations (scatter plots and surfaces)
from potential field data.
"""

import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import griddata


def calculate_aspect_ratio(lons, lats, potentials, z_scale=0.10):
    """
    Calculate proper aspect ratio for geographic data.

    Args:
        lons: Longitude values
        lats: Latitude values
        potentials: Potential values (used to normalize z-axis)
        z_scale: Height as fraction of horizontal span (default: 0.10 = 10%)

    Returns:
        tuple: (aspect_x, aspect_y, aspect_z, z_normalization_factor)
    """
    center_lat = np.mean(lats)
    lon_span = lons.max() - lons.min()
    lat_span = lats.max() - lats.min()

    # At center latitude, 1 degree longitude = cos(lat) * 69 miles
    # 1 degree latitude = 69.172 miles
    lon_to_lat_ratio = np.cos(np.radians(center_lat))

    # Normalize so largest horizontal dimension = 1.0
    max_horiz = max(lon_span * lon_to_lat_ratio, lat_span)

    aspect_x = (lon_span * lon_to_lat_ratio) / max_horiz
    aspect_y = lat_span / max_horiz

    # Calculate z normalization: scale max potential to z_scale of horizontal span
    # We want: max(potentials) * z_norm = z_scale * max_horiz
    # Therefore: z_norm = (z_scale * max_horiz) / max(potentials)
    max_potential = potentials.max()
    z_normalization = (z_scale * max_horiz) / max_potential

    # Aspect ratio for z is then: (max_potential * z_norm) / max_horiz = z_scale
    aspect_z = z_scale

    return aspect_x, aspect_y, aspect_z, z_normalization


def create_scatter_3d(lons, lats, potentials, title="Population Potential Field",
                      colorscale='Jet', color_mode='linear', marker_size=3,
                      z_scale=0.10, z_mode='linear', width=1400, height=900):
    """
    Create 3D scatter plot of potential field.

    Args:
        lons: Longitude values
        lats: Latitude values
        potentials: Potential values
        title: Plot title
        colorscale: Plotly colorscale name (default: 'Jet')
        color_mode: 'linear' or 'log' (default: 'linear')
        marker_size: Size of scatter points (default: 3)
        z_scale: Height as fraction of horizontal span (default: 0.10 = 10%)
        width: Plot width in pixels (default: 1400)
        height: Plot height in pixels (default: 900)

    Returns:
        plotly.graph_objects.Figure
    """
    # Apply z-mode transformation
    if z_mode == 'log':
        z_potentials = np.log10(potentials + 1)
    else:
        z_potentials = potentials

    # Calculate aspect ratio and z normalization
    aspect_x, aspect_y, aspect_z, z_norm = calculate_aspect_ratio(lons, lats, z_potentials, z_scale)

    # Normalize z values based on calculated normalization
    z_values = z_potentials * z_norm

    # Determine color values
    if color_mode == 'log':
        color_values = np.log10(potentials + 1)
        colorbar_title = "Log10(Potential)"
        tickformat = ',.1f'
    else:  # linear
        color_values = potentials
        colorbar_title = "Potential"
        tickformat = ',.0f'

    # Create scatter plot
    fig = go.Figure(data=[go.Scatter3d(
        x=lons,
        y=lats,
        z=z_values,
        mode='markers',
        marker=dict(
            size=marker_size,
            color=color_values,
            colorscale=colorscale,
            colorbar=dict(
                title=colorbar_title,
                tickformat=tickformat
            ),
            showscale=True,
            cmin=0 if color_mode == 'linear' else None,
            cmax=np.percentile(color_values, 99.5) if color_mode == 'linear' else None
        ),
        hovertemplate='Lon: %{x:.4f}<br>Lat: %{y:.4f}<br>Potential: %{customdata:,.0f}<extra></extra>',
        customdata=potentials
    )])

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            zaxis_title='Potential (normalized)',
            camera=dict(
                eye=dict(x=0.0, y=-2.5, z=1.5),  # North-facing: look from south
                center=dict(x=0, y=0, z=-0.1)
            ),
            aspectmode='manual',
            aspectratio=dict(x=aspect_x, y=aspect_y, z=aspect_z)
        ),
        width=width,
        height=height,
        margin=dict(l=0, r=0, b=0, t=40)
    )

    return fig


def create_surface_3d(lons, lats, potentials, title="Population Potential Field",
                      colorscale='Jet', color_mode='linear', grid_resolution=400,
                      interpolation='cubic', z_scale=0.10, z_mode='linear', width=1200, height=800):
    """
    Create 3D surface plot of potential field with interpolation.

    Args:
        lons: Longitude values (scattered points)
        lats: Latitude values (scattered points)
        potentials: Potential values
        title: Plot title
        colorscale: Plotly colorscale name (default: 'Jet')
        color_mode: 'linear' or 'log' (default: 'linear')
        grid_resolution: Number of grid points for interpolation (default: 400)
        interpolation: 'linear', 'cubic', or 'nearest' (default: 'cubic')
        z_scale: Height as fraction of horizontal span (default: 0.10 = 10%)
        width: Plot width in pixels (default: 1200)
        height: Plot height in pixels (default: 800)

    Returns:
        plotly.graph_objects.Figure
    """
    # Apply z-mode transformation
    if z_mode == 'log':
        z_potentials = np.log10(potentials + 1)
    else:
        z_potentials = potentials

    # Calculate aspect ratio and z normalization
    aspect_x, aspect_y, aspect_z, z_norm = calculate_aspect_ratio(lons, lats, z_potentials, z_scale)

    # Create regular grid
    lon_min, lon_max = lons.min(), lons.max()
    lat_min, lat_max = lats.min(), lats.max()

    # Calculate grid density based on aspect ratio
    lon_span = lon_max - lon_min
    lat_span = lat_max - lat_min

    if lon_span > lat_span:
        grid_lon = np.linspace(lon_min, lon_max, grid_resolution)
        grid_lat = np.linspace(lat_min, lat_max, int(grid_resolution * lat_span / lon_span))
    else:
        grid_lon = np.linspace(lon_min, lon_max, int(grid_resolution * lon_span / lat_span))
        grid_lat = np.linspace(lat_min, lat_max, grid_resolution)

    grid_lon_mesh, grid_lat_mesh = np.meshgrid(grid_lon, grid_lat)

    # Interpolate potentials to regular grid (use z_potentials for height)
    print(f"  Interpolating {len(lons)} points onto {len(grid_lon)}x{len(grid_lat)} grid...")
    grid_z_potential = griddata(
        (lons, lats),
        z_potentials,
        (grid_lon_mesh, grid_lat_mesh),
        method=interpolation,
        fill_value=0
    )

    # Also interpolate original potentials for coloring
    grid_potential = griddata(
        (lons, lats),
        potentials,
        (grid_lon_mesh, grid_lat_mesh),
        method=interpolation,
        fill_value=0
    )

    # Fill NaNs with nearest neighbor if present
    nan_mask = np.isnan(grid_z_potential)
    if np.any(nan_mask):
        print(f"  Filling {np.sum(nan_mask)} NaN values with nearest neighbor...")
        grid_z_nearest = griddata(
            (lons, lats),
            z_potentials,
            (grid_lon_mesh, grid_lat_mesh),
            method='nearest'
        )
        grid_z_potential[nan_mask] = grid_z_nearest[nan_mask]

        grid_potential_nearest = griddata(
            (lons, lats),
            potentials,
            (grid_lon_mesh, grid_lat_mesh),
            method='nearest'
        )
        grid_potential[nan_mask] = grid_potential_nearest[nan_mask]

    # Apply z normalization for display
    grid_z = grid_z_potential * z_norm

    # Determine surface color (use original potential values, not normalized)
    if color_mode == 'log':
        surfacecolor = np.log10(grid_potential + 1)
        colorbar_title = "Log10(Potential)"
        tickformat = '.2f'
    else:  # linear
        surfacecolor = grid_potential
        colorbar_title = "Potential"
        tickformat = ',.0f'

    # Create surface plot
    fig = go.Figure(data=[go.Surface(
        x=grid_lon_mesh,
        y=grid_lat_mesh,
        z=grid_z,
        surfacecolor=surfacecolor,
        colorscale=colorscale,
        colorbar=dict(
            title=colorbar_title,
            tickformat=tickformat
        ),
        hovertemplate='Lon: %{x:.2f}<br>Lat: %{y:.2f}<br>Potential: %{surfacecolor:,.0f}<extra></extra>'
    )])

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            zaxis_title='Potential (normalized)',
            camera=dict(
                eye=dict(x=0.0, y=-2.5, z=1.5),  # North-facing: look from south
                center=dict(x=0, y=0, z=-0.1)
            ),
            aspectmode='manual',
            aspectratio=dict(x=aspect_x, y=aspect_y, z=aspect_z)
        ),
        width=width,
        height=height,
        margin=dict(l=0, r=0, b=0, t=40)
    )

    return fig


def create_mesh_3d(lons, lats, potentials, title="Population Potential Field",
                   colorscale='Jet', color_mode='linear', z_scale=0.10, z_mode='linear',
                   width=1200, height=800):
    """
    Create 3D mesh plot (Delaunay triangulation) of potential field.

    Args:
        lons: Longitude values
        lats: Latitude values
        potentials: Potential values
        title: Plot title
        colorscale: Plotly colorscale name (default: 'Jet')
        color_mode: 'linear' or 'log' (default: 'linear')
        z_scale: Height as fraction of horizontal span (default: 0.10 = 10%)
        width: Plot width in pixels (default: 1200)
        height: Plot height in pixels (default: 800)

    Returns:
        plotly.graph_objects.Figure
    """
    # Apply z-mode transformation
    if z_mode == 'log':
        z_potentials = np.log10(potentials + 1)
    else:
        z_potentials = potentials

    # Calculate aspect ratio and z normalization
    aspect_x, aspect_y, aspect_z, z_norm = calculate_aspect_ratio(lons, lats, z_potentials, z_scale)

    # Normalize z values
    z_values = z_potentials * z_norm

    # Determine intensity values for coloring
    if color_mode == 'log':
        intensity = np.log10(potentials + 1)
        colorbar_title = "Log10(Potential)"
        tickformat = '.2f'
    else:  # linear
        intensity = potentials
        colorbar_title = "Potential"
        tickformat = ',.0f'

    # Create mesh with Delaunay triangulation
    fig = go.Figure(data=[go.Mesh3d(
        x=lons,
        y=lats,
        z=z_values,
        intensity=intensity,
        colorscale=colorscale,
        colorbar=dict(
            title=colorbar_title,
            tickformat=tickformat
        ),
        hovertemplate='Lon: %{x:.2f}<br>Lat: %{y:.2f}<br>Potential: %{customdata:,.0f}<extra></extra>',
        customdata=potentials,
        flatshading=False
    )])

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            zaxis_title='Potential (normalized)',
            camera=dict(
                eye=dict(x=0.0, y=-2.5, z=1.5),  # North-facing: look from south
                center=dict(x=0, y=0, z=-0.1)
            ),
            aspectmode='manual',
            aspectratio=dict(x=aspect_x, y=aspect_y, z=aspect_z)
        ),
        width=width,
        height=height,
        margin=dict(l=0, r=0, b=0, t=40)
    )

    return fig
