"""Tests for geometry functions."""
import pytest
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import geometry


def test_calculate_distances_simple():
    """Test distance calculation with known points."""
    # Two points 1 degree apart in longitude at equator
    # Should be ~69.17 miles
    lons = np.array([0.0, 1.0])
    lats = np.array([0.0, 0.0])

    distances = geometry.cos_corrected_distance(
        lons[0:1], lats[0:1],  # Sample point
        lons, lats,             # All points
        avg_lat=0.0
    )

    # First distance should be 0 (to itself)
    assert distances[0, 0] == pytest.approx(0.0, abs=0.001)
    # Second should be ~69.17 miles
    assert distances[0, 1] == pytest.approx(69.17, rel=0.01)


def test_calculate_distances_latitude():
    """Test latitude correction at 45 degrees."""
    # At 45°N, longitude distances are ~0.707x latitude distances
    lons = np.array([0.0, 1.0])
    lats = np.array([45.0, 45.0])

    distances = geometry.cos_corrected_distance(
        lons[0:1], lats[0:1],
        lons, lats,
        avg_lat=45.0
    )

    # Distance should be ~69.17 * cos(45°) ≈ 48.9 miles
    from lib.constants import MILES_PER_DEGREE
    expected = MILES_PER_DEGREE * np.cos(np.radians(45.0))
    assert distances[0, 1] == pytest.approx(expected, rel=0.01)


def test_calculate_distances_vectorized():
    """Test that vectorized calculation handles multiple points."""
    lons = np.array([-122.0, -121.0, -120.0])
    lats = np.array([37.0, 37.0, 37.0])

    # Calculate distances from first 2 points to all 3
    distances = geometry.cos_corrected_distance(
        lons[0:2], lats[0:2],
        lons, lats,
        avg_lat=37.0
    )

    # Should get 2x3 matrix
    assert distances.shape == (2, 3)
    # Diagonal-like elements should be 0
    assert distances[0, 0] == pytest.approx(0.0, abs=0.001)
    assert distances[1, 1] == pytest.approx(0.0, abs=0.001)


def test_haversine_distance():
    """Test Haversine distance calculation."""
    # SF to LA: approximately 347 miles
    sf_lon, sf_lat = -122.4194, 37.7749
    la_lon, la_lat = -118.2437, 34.0522

    sample_lons = np.array([sf_lon])
    sample_lats = np.array([sf_lat])
    source_lons = np.array([la_lon])
    source_lats = np.array([la_lat])

    distances = geometry.haversine_distance(
        sample_lons, sample_lats, source_lons, source_lats
    )

    # Should be approximately 347 miles
    assert distances[0, 0] == pytest.approx(347, abs=5)


def test_distance_functions_comparable():
    """Test that all distance functions give similar results for short distances."""
    # Short distance: 0.1 degrees at 37°N (~7 miles)
    sample_lons = np.array([-122.0])
    sample_lats = np.array([37.0])
    source_lons = np.array([-121.9])
    source_lats = np.array([37.0])

    d_cos = geometry.cos_corrected_distance(sample_lons, sample_lats, source_lons, source_lats)[0, 0]
    d_hav = geometry.haversine_distance(sample_lons, sample_lats, source_lons, source_lats)[0, 0]

    # Should agree within 1% for short distances
    np.testing.assert_allclose(d_cos, d_hav, rtol=0.01)
