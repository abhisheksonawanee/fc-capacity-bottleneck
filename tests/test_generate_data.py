"""Tests for data generation module."""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generate_data import generate_fc_data, save_raw_data
from src.utils import load_config, get_project_root


def test_deterministic_generation():
    """Test that data generation is deterministic with same random_state."""
    config = load_config()
    config['random_state'] = 42
    config['num_days'] = 7  # Small dataset for testing
    
    # Generate twice with same seed
    df1 = generate_fc_data(config)
    df2 = generate_fc_data(config)
    
    # Should be identical
    pd.testing.assert_frame_equal(df1, df2)


def test_generate_data_creates_file():
    """Test that data generation creates expected file."""
    config = load_config()
    config['random_state'] = 42
    config['num_days'] = 7
    
    project_root = get_project_root()
    output_file = project_root / config['data']['raw_file']
    
    # Clean up if exists
    if output_file.exists():
        output_file.unlink()
    
    # Generate and save
    df = generate_fc_data(config)
    save_raw_data(df, config=config)
    
    # Check file exists
    assert output_file.exists(), "Raw data file should be created"
    
    # Clean up
    if output_file.exists():
        output_file.unlink()


def test_generated_data_has_expected_columns():
    """Test that generated data has all expected columns."""
    config = load_config()
    config['random_state'] = 42
    config['num_days'] = 7
    
    df = generate_fc_data(config)
    
    expected_columns = [
        'timestamp', 'step', 'demand_units', 'capacity_units',
        'processed_units', 'backlog_units', 'utilization',
        'cycle_time_min', 'uph', 'labor_hours_used', 'headcount_used'
    ]
    
    for col in expected_columns:
        assert col in df.columns, f"Missing column: {col}"
    
    # Check that all steps are present
    assert set(df['step'].unique()) == set(config['steps']), "All steps should be present"


def test_generated_data_types():
    """Test that generated data has correct types."""
    config = load_config()
    config['random_state'] = 42
    config['num_days'] = 7
    
    df = generate_fc_data(config)
    
    # Check numeric columns
    numeric_cols = ['demand_units', 'capacity_units', 'processed_units',
                   'backlog_units', 'utilization', 'cycle_time_min',
                   'uph', 'labor_hours_used']
    
    for col in numeric_cols:
        assert pd.api.types.is_numeric_dtype(df[col]), f"{col} should be numeric"
    
    # Check headcount is integer
    assert pd.api.types.is_integer_dtype(df['headcount_used']), "headcount_used should be integer"
    
    # Check utilization is in [0, 1]
    assert (df['utilization'] >= 0).all(), "Utilization should be >= 0"
    assert (df['utilization'] <= 1).all(), "Utilization should be <= 1"

