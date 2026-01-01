"""Preprocess raw FC operations data."""

import pandas as pd
from pathlib import Path
from typing import Dict, Any

from .utils import load_config, ensure_dir, get_project_root


def load_raw_data(config: Dict[str, Any] = None) -> pd.DataFrame:
    """Load raw data from CSV.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        DataFrame with raw data
    """
    if config is None:
        config = load_config()
    
    project_root = get_project_root()
    raw_file = project_root / config['data']['raw_file']
    
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_file}. Run 'python run.py generate' first.")
    
    df = pd.read_csv(raw_file)
    return df


def validate_schema(df: pd.DataFrame) -> None:
    """Validate data schema and types.
    
    Args:
        df: DataFrame to validate
        
    Raises:
        ValueError: If schema is invalid
    """
    required_columns = [
        'timestamp', 'step', 'demand_units', 'capacity_units',
        'processed_units', 'backlog_units', 'utilization',
        'cycle_time_min', 'uph', 'labor_hours_used', 'headcount_used'
    ]
    
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Validate types
    if not pd.api.types.is_numeric_dtype(df['demand_units']):
        raise ValueError("demand_units must be numeric")
    if not pd.api.types.is_numeric_dtype(df['capacity_units']):
        raise ValueError("capacity_units must be numeric")
    if not pd.api.types.is_numeric_dtype(df['processed_units']):
        raise ValueError("processed_units must be numeric")


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived features from raw data.
    
    Args:
        df: Raw DataFrame
        
    Returns:
        DataFrame with additional features
    """
    df = df.copy()
    
    # Parse timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extract date components
    df['date'] = df['timestamp'].dt.date
    df['dow'] = df['timestamp'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['hour'] = df['timestamp'].dt.hour
    df['is_weekend'] = df['dow'] >= 5
    
    # Ensure numeric columns are numeric
    numeric_cols = ['demand_units', 'capacity_units', 'processed_units', 
                   'backlog_units', 'utilization', 'cycle_time_min',
                   'uph', 'labor_hours_used', 'headcount_used']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def preprocess_data(config: Dict[str, Any] = None) -> pd.DataFrame:
    """Main preprocessing function.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Cleaned DataFrame
    """
    if config is None:
        config = load_config()
    
    print("Loading raw data...")
    df = load_raw_data(config)
    
    print("Validating schema...")
    validate_schema(df)
    
    print("Creating features...")
    df = create_features(df)
    
    print(f"Preprocessed data shape: {df.shape}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Steps: {df['step'].unique().tolist()}")
    
    return df


def save_clean_data(df: pd.DataFrame, config: Dict[str, Any] = None) -> Path:
    """Save cleaned data to CSV.
    
    Args:
        df: Cleaned DataFrame
        config: Configuration dictionary
        
    Returns:
        Path to saved file
    """
    if config is None:
        config = load_config()
    
    project_root = get_project_root()
    output_file = project_root / config['data']['processed_file']
    ensure_dir(output_file.parent)
    
    df.to_csv(output_file, index=False)
    print(f"Saved cleaned data to: {output_file}")
    
    return output_file


def main():
    """Main entry point for preprocessing."""
    config = load_config()
    df = preprocess_data(config)
    save_clean_data(df, config)


if __name__ == "__main__":
    main()

