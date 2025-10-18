"""Geometric calculations: distances, triangulation."""
import numpy as np
from scipy.spatial import Delaunay


def calculate_distances(sample_lons, sample_lats, source_lons, source_lats, avg_lat):
    """
    Calculate pairwise distances between sample and source points.
    
    Uses cosine-corrected Euclidean distance (fast approximation).
    
    Parameters
    ----------
    sample_lons : ndarray (N,)
        Longitudes of sample points
    sample_lats : ndarray (N,)
        Latitudes of sample points
    source_lons : ndarray (M,)
        Longitudes of source points
    source_lats : ndarray (M,)
        Latitudes of source points
    avg_lat : float
        Average latitude for cosine correction
        
    Returns
    -------
    ndarray (N, M)
        Distance matrix in miles
    """
    cos_avg_lat = np.cos(np.radians(avg_lat))
    
    # Broadcast to get all pairwise distances
    # sample_lons[:, newaxis] creates (N, 1)
    # source_lons[newaxis, :] creates (1, M)
    # Result is (N, M)
    dlon = (sample_lons[:, np.newaxis] - source_lons[np.newaxis, :]) * cos_avg_lat
    dlat = sample_lats[:, np.newaxis] - source_lats[np.newaxis, :]
    
    # Euclidean distance in degrees, convert to miles
    distances = np.sqrt(dlon**2 + dlat**2) * 69.0
    
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
