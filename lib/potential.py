"""Core potential calculation functions."""
import numpy as np


def calculate_potential(distances, weights, 
                       force_exponent=3,
                       contribution_cap=500000,
                       exclude_closest_n=0,
                       max_distance_miles=None):
    """
    Calculate potential at sample points from weighted source points.
    
    Parameters
    ----------
    distances : ndarray (N, M)
        Distance matrix: N sample points × M source points (in miles)
    weights : ndarray (M,)
        Weights (populations) of source points
    force_exponent : int
        Exponent for 1/d^n potential (default: 3)
    contribution_cap : float or None
        Cap individual contributions to prevent singularities
    exclude_closest_n : int
        Exclude N closest neighbors from each sample point
    max_distance_miles : float or None
        Zero contribution beyond this distance
        
    Returns
    -------
    ndarray (N,)
        Potential values at sample points
    """
    # Avoid division by zero
    distances_safe = np.maximum(distances, 0.001)
    
    # Calculate raw contributions: weight / distance^exponent
    contributions = weights[np.newaxis, :] / (distances_safe ** force_exponent)
    
    # Apply contribution cap if specified
    if contribution_cap is not None:
        contributions = np.minimum(contributions, contribution_cap)
    
    # Create mask for which contributions to include
    mask = np.ones_like(distances, dtype=bool)
    
    # Exclude closest N neighbors
    if exclude_closest_n > 0:
        # For each sample point, find indices of N closest sources
        sorted_indices = np.argsort(distances, axis=1)
        for i in range(len(distances)):
            closest_indices = sorted_indices[i, :exclude_closest_n]
            mask[i, closest_indices] = False
    
    # Exclude beyond max distance
    if max_distance_miles is not None:
        mask &= (distances <= max_distance_miles)
    
    # Apply mask and sum
    contributions_masked = contributions * mask
    potentials = np.sum(contributions_masked, axis=1)
    
    return potentials
