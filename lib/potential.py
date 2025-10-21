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
        REQUIRED to be > 0 if any sample point exactly matches a source point.

    Returns
    -------
    ndarray (N,)
        Potential values at sample points

    Raises
    ------
    ValueError
        If any distance is exactly 0 and min_distance_miles is 0
    """
    # Check for division by zero
    if min_distance_miles == 0 and np.any(distances == 0):
        raise ValueError(
            "Sample point(s) exactly match source point(s) (distance=0). "
            "Set min_distance_miles > 0 to avoid singularity. "
            "Typical values: 0.5-1.0 miles for census centroids."
        )

    # Apply minimum distance clamping if specified
    if min_distance_miles > 0:
        distances_safe = np.maximum(distances, min_distance_miles)
    else:
        distances_safe = distances

    # Calculate raw contributions: weight / distance^exponent
    contributions = weights[np.newaxis, :] / (distances_safe ** force_exponent)

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
                                min_distance_miles=0.0, max_distance_miles=None,
                                n_jobs=1):
    """
    Calculate potential at sample points from source points using chunked processing.

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
        REQUIRED to be > 0 if any sample point exactly matches a source point.
    max_distance_miles : float or None
        Maximum distance to include (default: None = no cutoff).
        Sources beyond this distance contribute zero potential.
        Use 50-100 to limit calculation to local influences only.
    n_jobs : int
        Number of parallel jobs (default: 1 = sequential).
        Use -1 for all available cores.

    Returns
    -------
    ndarray (N,)
        Potential values at sample points

    Raises
    ------
    ValueError
        If any sample point exactly matches a source point and min_distance_miles is 0
    """
    num_samples = len(sample_lons)
    potentials = np.zeros(num_samples)

    # Pre-calculate avg_lat for consistency across chunks
    # (for distance functions that need it like cos_corrected_distance)
    all_lats = np.concatenate([sample_lats, source_lats])
    avg_lat = np.mean(all_lats)

    # Process in chunks
    num_chunks = (num_samples + chunk_size - 1) // chunk_size

    # Define chunk processing function
    def process_chunk(chunk_idx):
        """Process a single chunk and return (start_idx, end_idx, chunk_potentials)."""
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

        # Check for division by zero
        if min_distance_miles == 0 and np.any(distances == 0):
            raise ValueError(
                "Sample point(s) exactly match source point(s) (distance=0). "
                "Set min_distance_miles > 0 to avoid singularity. "
                "Typical values: 0.5-1.0 miles for census centroids."
            )

        # Apply minimum distance clamping if specified
        if min_distance_miles > 0:
            distances_safe = np.maximum(distances, min_distance_miles)
        else:
            distances_safe = distances

        # Calculate contributions: weight / distance^exponent
        contributions = source_weights[np.newaxis, :] / (distances_safe ** force_exponent)

        # Apply max distance cutoff if specified
        if max_distance_miles is not None:
            beyond_max = (distances > max_distance_miles)
            contributions = np.where(beyond_max, 0.0, contributions)

        # Sum contributions for each sample point in this chunk
        chunk_potentials = np.sum(contributions, axis=1)
        return (start_idx, end_idx, chunk_potentials)

    # Process chunks (parallel or sequential)
    if n_jobs == 1:
        # Sequential processing
        for chunk_idx in range(num_chunks):
            start_idx, end_idx, chunk_potentials = process_chunk(chunk_idx)
            potentials[start_idx:end_idx] = chunk_potentials
    else:
        # Parallel processing
        from joblib import Parallel, delayed
        print(f"  Processing {num_chunks} chunks with {n_jobs} parallel jobs...")
        results = Parallel(n_jobs=n_jobs, verbose=10)(
            delayed(process_chunk)(chunk_idx) for chunk_idx in range(num_chunks)
        )
        for start_idx, end_idx, chunk_potentials in results:
            potentials[start_idx:end_idx] = chunk_potentials

    return potentials
