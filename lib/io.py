"""I/O functions for loading and saving data."""
import pandas as pd
from pathlib import Path


def load_csv(filepath, lon_col='LONGITUDE', lat_col='LATITUDE', weight_col='POPULATION'):
    """
    Load point data from CSV file.
    
    Parameters
    ----------
    filepath : str
        Path to CSV file
    lon_col : str
        Name of longitude column
    lat_col : str
        Name of latitude column
    weight_col : str
        Name of weight/population column
        
    Returns
    -------
    pd.DataFrame
        DataFrame with point data
        
    Raises
    ------
    FileNotFoundError
        If file doesn't exist
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Validate required columns exist
    required = [lon_col, lat_col, weight_col]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    return df
