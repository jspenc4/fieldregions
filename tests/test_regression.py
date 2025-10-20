"""Regression tests against verified baselines."""
import pytest
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import io, potential, geometry


def test_sf_bay_regression():
    """Ensure SF Bay results match verified baseline."""
    # Load data
    df = io.load_csv('res/tracts_sf_bay.csv')
    lons = df['LONGITUDE'].values
    lats = df['LATITUDE'].values
    weights = df['POPULATION'].values

    # Calculate potential (with min_distance to smooth census centroid noise)
    potentials = potential.calculate_potential_chunked(
        lons, lats, lons, lats, weights,
        geometry.haversine_distance,
        force_exponent=3,
        min_distance_miles=0.5  # Required when sampling at source points
    )

    # Load baseline
    baseline = np.load('test_data/baseline_sf_bay.npy')

    # Should match exactly (or very close due to floating point)
    np.testing.assert_allclose(potentials, baseline, rtol=1e-6)

    # Sanity checks on magnitudes (with min_distance=0.5)
    assert potentials.min() > 0
    assert potentials.max() < 1_000_000  # Peak ~770k (includes self-contribution)
    assert potentials.mean() > 100_000
    assert potentials.mean() < 200_000
