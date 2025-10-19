"""Core potential calculation functions."""
import numpy as np


def calculate_potential(distances, weights,
                       force_exponent=3,
                       max_distance_miles=None,
                       min_distance_miles=0):
    """
    Calculate potential at sample points from weighted source points.

    Takes pre-computed distance matrix. For most use cases, use
    calculate_potential_chunked() instead for better memory efficiency.

    Parameters
    ----------
    distances : ndarray (N, M)
        Distance matrix: N sample points × M source points (in miles)
    weights : ndarray (M,)
        Weights (populations) of source points
    force_exponent : int
        Exponent for 1/d^n potential (default: 3)
    max_distance_miles : float or None
        Zero contribution beyond this distance (default: None)
    min_distance_miles : float
        Minimum distance for calculations (default: 0.0).
        Distances smaller than this are clamped to this value.
        When 0.0, no clamping is applied (self-contribution still excluded).

    Returns
    -------
    ndarray (N,)
        Potential values at sample points
    """
    # Detect self-contribution (exact distance = 0)
    is_self = (distances == 0)

    # Replace self with dummy value (will be zeroed out anyway)
    distances_safe = np.where(is_self, 1.0, distances)

    # Apply minimum distance clamping if specified
    if min_distance_miles > 0:
        distances_safe = np.maximum(distances_safe, min_distance_miles)

    # Calculate raw contributions: weight / distance^exponent
    contributions = weights[np.newaxis, :] / (distances_safe ** force_exponent)

    # Exclude self-contributions (set to zero)
    contributions = np.where(is_self, 0.0, contributions)

    # Apply max distance cutoff if specified
    if max_distance_miles is not None:
        beyond_max = (distances > max_distance_miles)
        contributions = np.where(beyond_max, 0.0, contributions)

    # Sum all contributions
    potentials = np.sum(contributions, axis=1)

    return potentials


def calculate_potential_chunked(sample_lons, sample_lats,
                                source_lons, source_lats, source_weights,
                                distance_fn, force_exponent=3, chunk_size=1000,
                                min_distance_miles=0.0, max_distance_miles=None):
    """
    Calculate potential at sample points from source points using chunked processing.

    Automatically excludes self-contribution when sample point exactly equals source point.

    Parameters
    ----------
    sample_lons, sample_lats : ndarray (N,)
        Locations where potential should be calculated
    source_lons, source_lats, source_weights : ndarray (M,)
        Source points that exert force
    distance_fn : callable
        Function to calculate distances: distance_fn(sample_lons, sample_lats, source_lons, source_lats) -> (N, M) array
    force_exponent : int
        Exponent for 1/d^n potential (default: 3)
    chunk_size : int
        Number of sample points to process at once (default: 1000)
    min_distance_miles : float
        Minimum distance for calculations (default: 0.0).
        Distances smaller than this are clamped to this value.
        Use 0.5-1.0 to smooth noise from approximate census centroids.
        When 0.0, no clamping is applied.
        Self-contribution (exact distance=0) is always excluded regardless.
    max_distance_miles : float or None
        Maximum distance to include (default: None = no cutoff).
        Sources beyond this distance contribute zero potential.
        Use 50-100 to limit calculation to local influences only.

    Returns
    -------
    ndarray (N,)
        Potential values at sample points (self-contribution excluded)
    """
    num_samples = len(sample_lons)
    potentials = np.zeros(num_samples)

    # Pre-calculate avg_lat for consistency across chunks
    # (for distance functions that need it like cos_corrected_distance)
    all_lats = np.concatenate([sample_lats, source_lats])
    avg_lat = np.mean(all_lats)

    # Process in chunks
    num_chunks = (num_samples + chunk_size - 1) // chunk_size

    for chunk_idx in range(num_chunks):
        start_idx = chunk_idx * chunk_size
        end_idx = min(start_idx + chunk_size, num_samples)

        # Get chunk of sample points
        chunk_lons = sample_lons[start_idx:end_idx]
        chunk_lats = sample_lats[start_idx:end_idx]

        # Calculate distances using provided function
        # Result: (chunk_size, num_sources) distance matrix
        # Try passing avg_lat if the function accepts it
        try:
            distances = distance_fn(chunk_lons, chunk_lats, source_lons, source_lats, avg_lat)
        except TypeError:
            # Function doesn't take avg_lat parameter (e.g., haversine)
            distances = distance_fn(chunk_lons, chunk_lats, source_lons, source_lats)

        # Detect exact matches (self-contribution to exclude)
        is_self = (distances == 0)

        # Replace self with dummy value (will be zeroed out anyway)
        distances_safe = np.where(is_self, 1.0, distances)

        # Apply minimum distance clamping if specified
        if min_distance_miles > 0:
            distances_safe = np.maximum(distances_safe, min_distance_miles)

        # Calculate contributions: weight / distance^exponent
        contributions = source_weights[np.newaxis, :] / (distances_safe ** force_exponent)

        # Exclude self-contributions (set to zero)
        contributions = np.where(is_self, 0.0, contributions)

        # Apply max distance cutoff if specified
        if max_distance_miles is not None:
            beyond_max = (distances > max_distance_miles)
            contributions = np.where(beyond_max, 0.0, contributions)

        # Sum contributions for each sample point in this chunk
        potentials[start_idx:end_idx] = np.sum(contributions, axis=1)

    return potentials
