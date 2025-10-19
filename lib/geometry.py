"""Geometric calculations: distances, triangulation."""
import numpy as np
from scipy.spatial import Delaunay
from .constants import MILES_PER_DEGREE, EARTH_RADIUS_MILES


def cos_corrected_distance(sample_lons, sample_lats, source_lons, source_lats, avg_lat=None):
    """
    Calculate distances using cosine-corrected Euclidean approximation.

    Fast and accurate enough for visualization. Uses average latitude
    for cosine correction.

    Parameters
    ----------
    sample_lons, sample_lats : ndarray (N,)
        Sample point coordinates
    source_lons, source_lats : ndarray (M,)
        Source point coordinates
    avg_lat : float, optional
        Average latitude for cosine correction. If None, calculated from all points.

    Returns
    -------
    ndarray (N, M)
        Distance matrix in miles
    """
    # Auto-calculate average latitude if not provided
    if avg_lat is None:
        all_lats = np.concatenate([sample_lats, source_lats])
        avg_lat = np.mean(all_lats)

    cos_avg_lat = np.cos(np.radians(avg_lat))

    # Broadcast to get all pairwise distances
    dlon = (sample_lons[:, np.newaxis] - source_lons[np.newaxis, :]) * cos_avg_lat
    dlat = sample_lats[:, np.newaxis] - source_lats[np.newaxis, :]

    # Euclidean distance in degrees, convert to miles
    distances = np.sqrt(dlon**2 + dlat**2) * MILES_PER_DEGREE

    return distances


def haversine_distance(sample_lons, sample_lats, source_lons, source_lats):
    """
    Calculate distances using the Haversine formula.

    Most accurate for geographic coordinates but ~3x slower than cosine-corrected.
    Use when accuracy is critical.

    Parameters
    ----------
    sample_lons, sample_lats : ndarray (N,)
        Sample point coordinates
    source_lons, source_lats : ndarray (M,)
        Source point coordinates

    Returns
    -------
    ndarray (N, M)
        Distance matrix in miles
    """
    # Earth radius in miles
    R = EARTH_RADIUS_MILES

    # Convert to radians
    lat1 = np.radians(sample_lats[:, np.newaxis])
    lat2 = np.radians(source_lats[np.newaxis, :])
    lon1 = np.radians(sample_lons[:, np.newaxis])
    lon2 = np.radians(source_lons[np.newaxis, :])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distances = R * c

    return distances




def triangulate(points):
    """
    Create Delaunay triangulation of points.
    
    Parameters
    ----------
    points : ndarray (N, 2)
        Points as [lon, lat] pairs
        
    Returns
    -------
    scipy.spatial.Delaunay
        Triangulation object
    """
    return Delaunay(points)


def calculate_triangle_centers(points, triangulation):
    """
    Calculate centers of all triangles.
    
    Parameters
    ----------
    points : ndarray (N, 2)
        Points as [lon, lat] pairs
    triangulation : scipy.spatial.Delaunay
        Triangulation of points
        
    Returns
    -------
    ndarray (M, 2)
        Triangle centers as [lon, lat] pairs
    """
    centers = []
    for simplex in triangulation.simplices:
        vertices = points[simplex]
        center = vertices.mean(axis=0)
        centers.append(center)
    
    return np.array(centers)
