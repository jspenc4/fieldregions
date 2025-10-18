"""Tests for I/O functions."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import io


def test_load_csv_basic():
    """Test loading a basic CSV file."""
    df = io.load_csv('test_data/tiny.csv')
    
    assert len(df) == 10
    assert 'LONGITUDE' in df.columns
    assert 'LATITUDE' in df.columns
    assert 'POPULATION' in df.columns


def test_load_csv_extracts_arrays():
    """Test that we can extract numpy arrays."""
    df = io.load_csv('test_data/tiny.csv')
    
    lons = df['LONGITUDE'].values
    lats = df['LATITUDE'].values
    pops = df['POPULATION'].values
    
    assert len(lons) == 10
    assert isinstance(lons, np.ndarray)
    assert lons[0] == pytest.approx(-122.4194)
    assert pops[0] == 100000


def test_load_csv_missing_file():
    """Test handling of missing file."""
    with pytest.raises(FileNotFoundError):
        io.load_csv('does_not_exist.csv')
