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
        distances, weights, force_exponent=3
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
        distances, weights, force_exponent=3
    )

    expected = 1000/1000 + 2000/8000 + 3000/27000
    assert pot[0] == pytest.approx(expected, rel=0.01)


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
    )

    # Should match closely when there's no overlap
    # Note: Small difference due to auto-calculated avg_lat vs fixed avg_lat
    np.testing.assert_allclose(pot_chunked, pot_regular, rtol=0.002)


def test_calculate_potential_chunked_self():
    """Test that error is raised when sampling at source point without min_distance."""
    # Sample points = source points (calculating at census tract centroids)
    lons = np.array([-122.0, -122.1, -122.2])
    lats = np.array([37.5, 37.6, 37.7])
    weights = np.array([1000.0, 2000.0, 1500.0])

    # Should raise error when min_distance=0 and sampling at source points
    with pytest.raises(ValueError, match="exactly match source point"):
        potential.calculate_potential_chunked(
            lons, lats, lons, lats, weights,
            geometry.cos_corrected_distance,
            force_exponent=3,
            min_distance_miles=0
        )

    # Should work fine with min_distance > 0
    pot = potential.calculate_potential_chunked(
        lons, lats, lons, lats, weights,
        geometry.cos_corrected_distance,
        force_exponent=3,
        min_distance_miles=0.5
    )

    # All should be finite and positive
    assert np.all(np.isfinite(pot))
    assert np.all(pot > 0)


def test_calculate_potential_chunked_vs_scalar_loop():
    """Test vectorized/chunked calculation matches simple scalar loop."""
    # Small dataset for scalar loop - sample points different from source points
    sample_lons = np.array([-122.02, -122.12, -122.22])  # Offset from sources
    sample_lats = np.array([37.52, 37.62, 37.72])
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
    pot1 = potential.calculate_potential(distances, weights, force_exponent=1)
    expected1 = 1000.0/10.0 + 2000.0/20.0  # = 100 + 100 = 200
    assert pot1[0] == pytest.approx(expected1, rel=0.01)

    # Test exponent=2
    pot2 = potential.calculate_potential(distances, weights, force_exponent=2)
    expected2 = 1000.0/100.0 + 2000.0/400.0  # = 10 + 5 = 15
    assert pot2[0] == pytest.approx(expected2, rel=0.01)

    # Test exponent=3 (default: 1/d^4 force, 1/d^3 potential)
    pot3 = potential.calculate_potential(distances, weights, force_exponent=3)
    expected3 = 1000.0/1000.0 + 2000.0/8000.0  # = 1.0 + 0.25 = 1.25
    assert pot3[0] == pytest.approx(expected3, rel=0.01)

    # Test exponent=4
    pot4 = potential.calculate_potential(distances, weights, force_exponent=4)
    expected4 = 1000.0/10000.0 + 2000.0/160000.0  # = 0.1 + 0.0125 = 0.1125
    assert pot4[0] == pytest.approx(expected4, rel=0.01)


def test_calculate_potential_chunked_min_distance():
    """Test min_distance_miles parameter in chunked calculation."""
    # Very close points (simulating census centroid noise)
    # Offset sample points slightly to avoid exact match with sources
    sample_lons = np.array([-122.0001, -122.0011])  # Very close to sources
    sample_lats = np.array([37.0001, 37.0001])
    source_lons = np.array([-122.0, -122.001, -122.1])
    source_lats = np.array([37.0, 37.0, 37.0])
    source_weights = np.array([1000.0, 1000.0, 1000.0])

    # Without smoothing (very small distance, huge contributions)
    pot_no_smooth = potential.calculate_potential_chunked(
        sample_lons, sample_lats,
        source_lons, source_lats, source_weights,
        geometry.cos_corrected_distance,
        force_exponent=3,
        min_distance_miles=0
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
    # First point: very close to source 0 (~0.01 miles) and source 1 (~0.05 miles)
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


def test_self_contribution_with_min_distance():
    """Test that self-contribution is included when using min_distance smoothing."""
    # Create a simple case: sample point exactly matches a source point
    distances = np.array([[0.0, 10.0, 20.0]])  # First source is at same location
    weights = np.array([1000.0, 1000.0, 1000.0])

    # Without smoothing: should raise error
    with pytest.raises(ValueError, match="exactly match source point"):
        potential.calculate_potential(
            distances, weights, force_exponent=3, min_distance_miles=0
        )

    # With smoothing: self clamped to 1 mile (includes self-contribution)
    pot_smooth = potential.calculate_potential(
        distances, weights, force_exponent=3, min_distance_miles=1.0
    )
    # Expected: 1000/1.0^3 + 1000/10^3 + 1000/20^3 = 1000 + 1.0 + 0.125 = 1001.125
    expected_smooth = 1000.0 / (1.0 ** 3) + 1000.0 / (10.0 ** 3) + 1000.0 / (20.0 ** 3)
    assert pot_smooth[0] == pytest.approx(expected_smooth, rel=1e-10)


def test_calculate_potential_chunked_max_distance():
    """Test max_distance_miles parameter in chunked calculation."""
    # Points at various distances - use close sources where cutoff matters
    # Offset sample point to avoid exact match with first source
    sample_lons = np.array([-122.001])
    sample_lats = np.array([37.001])
    source_lons = np.array([-122.0, -122.02, -122.05, -122.2])  # ~0.1, 1.4, 3.5, 14 miles
    source_lats = np.array([37.0, 37.0, 37.0, 37.0])
    source_weights = np.array([1000.0, 1000.0, 1000.0, 1000.0])

    # No distance limit
    pot_unlimited = potential.calculate_potential_chunked(
        sample_lons, sample_lats,
        source_lons, source_lats, source_weights,
        geometry.cos_corrected_distance,
        force_exponent=3
    )

    # Limit to 5 miles (excludes the 14-mile source)
    pot_limited = potential.calculate_potential_chunked(
        sample_lons, sample_lats,
        source_lons, source_lats, source_weights,
        geometry.cos_corrected_distance,
        force_exponent=3,
        max_distance_miles=5.0
    )

    # Limited should exclude the farthest source
    assert pot_limited[0] < pot_unlimited[0]

    # Verify parameters are working (any difference proves it)
    assert abs(pot_unlimited[0] - pot_limited[0]) > 0.001


def test_min_distance_vs_no_smoothing():
    """Test that min_distance actually changes results significantly."""
    # Create scenario where smoothing matters: very close points
    sample_lons = np.array([-122.0])
    sample_lats = np.array([37.0])
    # Source very close (simulating census tract pair like Las Vegas artifact)
    source_lons = np.array([-122.0001])  # ~0.02 miles away
    source_lats = np.array([37.0])
    source_weights = np.array([10000.0])

    # No smoothing: huge potential from close source
    pot_no_smooth = potential.calculate_potential_chunked(
        sample_lons, sample_lats,
        source_lons, source_lats, source_weights,
        geometry.cos_corrected_distance,
        force_exponent=3,
        min_distance_miles=0.0
    )

    # With smoothing: clamped to 1 mile
    pot_smooth = potential.calculate_potential_chunked(
        sample_lons, sample_lats,
        source_lons, source_lats, source_weights,
        geometry.cos_corrected_distance,
        force_exponent=3,
        min_distance_miles=1.0
    )

    # Smoothing should dramatically reduce the potential
    # 10000 / 0.02^3 = 125,000,000 vs 10000 / 1.0^3 = 10,000
    assert pot_no_smooth[0] > pot_smooth[0] * 100  # At least 100x difference
    assert pot_smooth[0] == pytest.approx(10000.0, rel=0.01)  # Clamped to 1 mile
