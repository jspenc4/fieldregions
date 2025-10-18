"""Tests for potential calculation."""
import pytest
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import potential


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


def test_calculate_potential_exclude_closest():
    """Test excluding closest neighbors."""
    distances = np.array([[1.0, 5.0, 10.0, 20.0]])
    weights = np.array([1000.0, 1000.0, 1000.0, 1000.0])
    
    # Exclude 2 closest (1.0 and 5.0)
    pot = potential.calculate_potential(
        distances, weights, 
        force_exponent=3,
        exclude_closest_n=2,
        contribution_cap=None
    )
    
    # Should only include 10.0 and 20.0
    expected = 1000/1000 + 1000/8000
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
