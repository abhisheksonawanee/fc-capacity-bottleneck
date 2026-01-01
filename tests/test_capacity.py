"""Tests for capacity analytics module."""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.capacity import compute_capacity_metrics, save_capacity_metrics
from src.utils import load_config, get_project_root


def test_utilization_in_range():
    """Test that utilization is in [0, 1]."""
    # First generate and preprocess data if needed
    from src.generate_data import generate_fc_data, save_raw_data
    from src.preprocess import preprocess_data, save_clean_data
    
    config = load_config()
    config['random_state'] = 42
    config['num_days'] = 7
    
    project_root = get_project_root()
    
    # Generate data if not exists
    raw_file = project_root / config['data']['raw_file']
    if not raw_file.exists():
        df = generate_fc_data(config)
        save_raw_data(df, config=config)
    
    # Preprocess if not exists
    processed_file = project_root / config['data']['processed_file']
    if not processed_file.exists():
        df = preprocess_data(config)
        save_clean_data(df, config)
    
    # Compute metrics
    metrics = compute_capacity_metrics(config)
    
    # Check utilization
    assert 'utilization' in metrics['hourly'].columns
    assert (metrics['hourly']['utilization'] >= 0).all(), "Utilization should be >= 0"
    assert (metrics['hourly']['utilization'] <= 1).all(), "Utilization should be <= 1"


def test_capacity_outputs_created():
    """Test that capacity metrics outputs are created."""
    from src.generate_data import generate_fc_data, save_raw_data
    from src.preprocess import preprocess_data, save_clean_data
    
    config = load_config()
    config['random_state'] = 42
    config['num_days'] = 7
    
    project_root = get_project_root()
    
    # Generate data if not exists
    raw_file = project_root / config['data']['raw_file']
    if not raw_file.exists():
        df = generate_fc_data(config)
        save_raw_data(df, config=config)
    
    # Preprocess if not exists
    processed_file = project_root / config['data']['processed_file']
    if not processed_file.exists():
        df = preprocess_data(config)
        save_clean_data(df, config)
    
    # Compute and save metrics
    metrics = compute_capacity_metrics(config)
    save_capacity_metrics(metrics, config)
    
    # Check files exist
    hourly_file = project_root / config['data']['step_hourly_file']
    daily_step_file = project_root / config['data']['step_daily_file']
    site_daily_file = project_root / config['data']['site_daily_file']
    
    assert hourly_file.exists(), "Hourly metrics file should be created"
    assert daily_step_file.exists(), "Daily step metrics file should be created"
    assert site_daily_file.exists(), "Site daily metrics file should be created"

