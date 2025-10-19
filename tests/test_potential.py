"""Tests for potential calculation."""
import pytest
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import potential, geometry


def test_calculate_potential_single_point():
    """Test potential from a single source point."""
    distances = np.array([[10.0]])  # 10 miles away
    weights = np.array([1000.0])
    
    # With force_exponent=3: potential = 1000 / 10^3 = 1.0
    pot = potential.calculate_potential(
        distances, weights, force_exponent=3, contribution_cap=None
    )
    
    assert pot[0] == pytest.approx(1.0)


def test_calculate_potential_multiple_sources():
    """Test potential from multiple sources."""
    # Sample point distances to 3 sources
    distances = np.array([[10.0, 20.0, 30.0]])
    weights = np.array([1000.0, 2000.0, 3000.0])
    
    # Contributions: 1000/10^3 + 2000/20^3 + 3000/30^3
    # = 1.0 + 0.25 + 0.111... ≈ 1.361
    pot = potential.calculate_potential(
        distances, weights, force_exponent=3, contribution_cap=None
    )
    
    expected = 1000/1000 + 2000/8000 + 3000/27000
    assert pot[0] == pytest.approx(expected, rel=0.01)


def test_calculate_potential_with_cap():
    """Test contribution capping."""
    # Very close point should be capped
    distances = np.array([[0.01, 10.0]])  # First very close
    weights = np.array([1000.0, 1000.0])
    
    pot = potential.calculate_potential(
        distances, weights, force_exponent=3, contribution_cap=5000.0
    )
    
    # First contribution would be huge without cap, should be capped
    # Second contribution: 1000/1000 = 1.0
    # Total should be 5000 + 1.0 = 5001.0
    assert pot[0] > 5000.0  # Capped contribution included
    assert pot[0] < 6000.0  # But not unreasonably large


def test_calculate_potential_min_distance():
    """Test minimum distance clamping."""
    # Points at various distances including very close
    distances = np.array([[0.1, 0.5, 10.0, 20.0]])  # 0.1 and 0.5 miles very close
    weights = np.array([1000.0, 1000.0, 1000.0, 1000.0])

    # Clamp to 1.0 mile minimum (smooth census centroid noise)
    pot = potential.calculate_potential(
        distances, weights,
        force_exponent=3,
        min_distance_miles=1.0,
        contribution_cap=None
    )

    # First two are clamped to 1.0, others use actual distance
    # 1000/1.0^3 + 1000/1.0^3 + 1000/10.0^3 + 1000/20.0^3
    expected = 1000.0 + 1000.0 + 1.0 + 0.125
    assert pot[0] == pytest.approx(expected, rel=0.01)


def test_calculate_potential_max_distance():
    """Test max distance cutoff."""
    distances = np.array([[5.0, 10.0, 60.0]])  # Last beyond cutoff
    weights = np.array([1000.0, 1000.0, 1000.0])
    
    pot = potential.calculate_potential(
        distances, weights,
        force_exponent=3,
        max_distance_miles=50.0,
        contribution_cap=None
    )
    
    # Should only include first two (within 50 miles)
    expected = 1000/125 + 1000/1000
    assert pot[0] == pytest.approx(expected, rel=0.01)


def test_calculate_potential_chunked_simple():
    """Test chunked calculation with hand-verified result."""
    # Simple case: 1 sample point, 1 source point at known distance
    # At latitude 45°N, 1 degree lon ≈ 49 miles (cos(45°) ≈ 0.707)
    # 1 degree lat ≈ 69 miles
    sample_lons = np.array([-122.0])
    sample_lats = np.array([45.0])
    source_lons = np.array([-121.0])  # 1 degree east
    source_lats = np.array([45.0])     # same latitude
    source_weights = np.array([1000.0])

    pot = potential.calculate_potential_chunked(
        sample_lons, sample_lats,
        source_lons, source_lats, source_weights,
        geometry.cos_corrected_distance,
        force_exponent=3
    )

    # Distance should be ~1 degree * cos(45°) * 69.17 ≈ 48.9 miles
    # Potential = 1000 / 48.9^3 ≈ 0.00857
    # Using exact calculation: avg_lat = 45.0 (auto-calculated)
    from lib.constants import MILES_PER_DEGREE
    cos_45 = np.cos(np.radians(45.0))
    distance = 1.0 * cos_45 * MILES_PER_DEGREE  # ~48.9 miles
    expected = 1000.0 / (distance ** 3)

    assert pot[0] == pytest.approx(expected, rel=0.001)


def test_calculate_potential_chunked_no_overlap():
    """Test chunked calculation with non-overlapping sample/source points."""
    # Sample points and source points do NOT overlap
    sample_lons = np.array([-122.5, -122.6])  # Different from sources
    sample_lats = np.array([37.5, 37.6])
    source_lons = np.array([-122.0, -122.05, -122.1, -122.15])
    source_lats = np.array([37.5, 37.55, 37.6, 37.65])
    source_weights = np.array([1000.0, 2000.0, 1500.0, 3000.0])
    avg_lat = 37.6

    # Calculate using chunked method
    pot_chunked = potential.calculate_potential_chunked(
        sample_lons, sample_lats,
        source_lons, source_lats, source_weights,
        geometry.cos_corrected_distance,
        force_exponent=3, chunk_size=1  # Small chunks to test chunking
    )

    # Calculate using regular method for comparison
    distances = geometry.cos_corrected_distance(
        sample_lons, sample_lats, source_lons, source_lats, avg_lat
    )
    pot_regular = potential.calculate_potential(
        distances, source_weights, force_exponent=3,
        contribution_cap=None, max_distance_miles=None
    )

    # Should match closely when there's no overlap
    # Note: Small difference due to auto-calculated avg_lat vs fixed avg_lat
    np.testing.assert_allclose(pot_chunked, pot_regular, rtol=0.002)


def test_calculate_potential_chunked_self():
    """Test that self-contribution is excluded."""
    # Sample points = source points (calculating at census tract centroids)
    # Each point should get contribution from the other two, but not itself
    lons = np.array([-122.0, -122.1, -122.2])
    lats = np.array([37.5, 37.6, 37.7])
    weights = np.array([1000.0, 2000.0, 1500.0])

    pot = potential.calculate_potential_chunked(
        lons, lats, lons, lats, weights,
        geometry.cos_corrected_distance,
        force_exponent=3
    )

    # All should be finite (self excluded)
    assert np.all(np.isfinite(pot))
    assert np.all(pot > 0)  # All positive

    # Each point gets contributions from 2 others (not itself)
    # Verify manually for first point: contribution from points 1 and 2
    dist_01 = geometry.cos_corrected_distance(
        np.array([lons[0]]), np.array([lats[0]]),
        np.array([lons[1]]), np.array([lats[1]])
    )[0,0]
    dist_02 = geometry.cos_corrected_distance(
        np.array([lons[0]]), np.array([lats[0]]),
        np.array([lons[2]]), np.array([lats[2]])
    )[0,0]
    expected_0 = weights[1] / (dist_01 ** 3) + weights[2] / (dist_02 ** 3)

    assert pot[0] == pytest.approx(expected_0, rel=0.001)


def test_calculate_potential_chunked_vs_scalar_loop():
    """Test vectorized/chunked calculation matches simple scalar loop."""
    # Small dataset for scalar loop
    sample_lons = np.array([-122.0, -122.1, -122.2])
    sample_lats = np.array([37.5, 37.6, 37.7])
    source_lons = np.array([-122.0, -122.05, -122.1, -122.15])
    source_lats = np.array([37.5, 37.55, 37.6, 37.65])
    source_weights = np.array([1000.0, 2000.0, 1500.0, 3000.0])

    # Vectorized/chunked version (production code)
    pot_fast = potential.calculate_potential_chunked(
        sample_lons, sample_lats,
        source_lons, source_lats, source_weights,
        geometry.cos_corrected_distance,
        force_exponent=3,
        chunk_size=2  # Small chunks to test chunking logic
    )

    # Naive scalar loop (obviously correct, reference implementation)
    # Calculate global avg_lat same way as vectorized version
    all_lats = np.concatenate([sample_lats, source_lats])
    avg_lat = np.mean(all_lats)

    pot_slow = np.zeros(len(sample_lons))
    for i in range(len(sample_lons)):
        for j in range(len(source_lons)):
            # Skip self-contribution
            if sample_lons[i] == source_lons[j] and sample_lats[i] == source_lats[j]:
                continue

            # Calculate distance for this pair using same global avg_lat
            dist = geometry.cos_corrected_distance(
                np.array([sample_lons[i]]), np.array([sample_lats[i]]),
                np.array([source_lons[j]]), np.array([source_lats[j]]),
                avg_lat  # Pass global avg_lat
            )[0, 0]

            # Add contribution
            pot_slow[i] += source_weights[j] / (dist ** 3)

    # Vectorized should match scalar loop very closely
    # Both use same global avg_lat now (fixed in calculate_potential_chunked)
    np.testing.assert_allclose(pot_fast, pot_slow, rtol=1e-10)


def test_calculate_potential_force_exponents():
    """Test potential calculation with different force exponents."""
    distances = np.array([[10.0, 20.0]])
    weights = np.array([1000.0, 2000.0])

    # Test exponent=1 (gravity: 1/d force, 1/d potential)
    pot1 = potential.calculate_potential(
        distances, weights, force_exponent=1, contribution_cap=None
    )
    expected1 = 1000.0/10.0 + 2000.0/20.0  # = 100 + 100 = 200
    assert pot1[0] == pytest.approx(expected1, rel=0.01)

    # Test exponent=2
    pot2 = potential.calculate_potential(
        distances, weights, force_exponent=2, contribution_cap=None
    )
    expected2 = 1000.0/100.0 + 2000.0/400.0  # = 10 + 5 = 15
    assert pot2[0] == pytest.approx(expected2, rel=0.01)

    # Test exponent=3 (default: 1/d^4 force, 1/d^3 potential)
    pot3 = potential.calculate_potential(
        distances, weights, force_exponent=3, contribution_cap=None
    )
    expected3 = 1000.0/1000.0 + 2000.0/8000.0  # = 1.0 + 0.25 = 1.25
    assert pot3[0] == pytest.approx(expected3, rel=0.01)

    # Test exponent=4
    pot4 = potential.calculate_potential(
        distances, weights, force_exponent=4, contribution_cap=None
    )
    expected4 = 1000.0/10000.0 + 2000.0/160000.0  # = 0.1 + 0.0125 = 0.1125
    assert pot4[0] == pytest.approx(expected4, rel=0.01)


def test_calculate_potential_chunked_min_distance():
    """Test min_distance_miles parameter in chunked calculation."""
    # Very close points (simulating census centroid noise)
    sample_lons = np.array([-122.0, -122.001])  # ~0.05 miles apart
    sample_lats = np.array([37.0, 37.0])
    source_lons = np.array([-122.0, -122.001, -122.1])
    source_lats = np.array([37.0, 37.0, 37.0])
    source_weights = np.array([1000.0, 1000.0, 1000.0])

    # Without smoothing (default min_distance=0)
    pot_no_smooth = potential.calculate_potential_chunked(
        sample_lons, sample_lats,
        source_lons, source_lats, source_weights,
        geometry.cos_corrected_distance,
        force_exponent=3
    )

    # With smoothing (min_distance=1 mile)
    pot_smooth = potential.calculate_potential_chunked(
        sample_lons, sample_lats,
        source_lons, source_lats, source_weights,
        geometry.cos_corrected_distance,
        force_exponent=3,
        min_distance_miles=1.0
    )

    # Smoothing should reduce the very large contributions from close points
    # First point: very close to source 0 (~0 miles) and source 1 (~0.05 miles)
    # Without smoothing: huge potential
    # With smoothing: capped to 1 mile
    assert pot_no_smooth[0] > pot_smooth[0]

    # Smoothed values should be reasonable (not dominated by close points)
    # Each source at 1 mile: 1000/1^3 = 1000, so ~3000 total for 3 sources
    assert pot_smooth[0] < 5000  # Much less than unsmoothed


def test_calculate_potential_different_sample_source():
    """Test with different sample and source points (e.g., triangle centers vs census tracts)."""
    # Source points: census tract centroids
    source_lons = np.array([-122.0, -122.05, -122.1, -122.15])
    source_lats = np.array([37.5, 37.55, 37.6, 37.65])
    source_weights = np.array([1000.0, 2000.0, 1500.0, 3000.0])

    # Sample points: different locations (e.g., triangle centers)
    sample_lons = np.array([-122.02, -122.08, -122.12])
    sample_lats = np.array([37.52, 37.58, 37.62])

    # Vectorized version
    pot_fast = potential.calculate_potential_chunked(
        sample_lons, sample_lats,
        source_lons, source_lats, source_weights,
        geometry.cos_corrected_distance,
        force_exponent=3
    )

    # Scalar loop for verification
    all_lats = np.concatenate([sample_lats, source_lats])
    avg_lat = np.mean(all_lats)

    pot_slow = np.zeros(len(sample_lons))
    for i in range(len(sample_lons)):
        for j in range(len(source_lons)):
            dist = geometry.cos_corrected_distance(
                np.array([sample_lons[i]]), np.array([sample_lats[i]]),
                np.array([source_lons[j]]), np.array([source_lats[j]]),
                avg_lat
            )[0, 0]
            pot_slow[i] += source_weights[j] / (dist ** 3)

    # Should match exactly (no self-contribution to exclude)
    np.testing.assert_allclose(pot_fast, pot_slow, rtol=1e-10)

    # All potentials should be finite and positive
    assert np.all(np.isfinite(pot_fast))
    assert np.all(pot_fast > 0)
