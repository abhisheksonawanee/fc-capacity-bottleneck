"""Tests for bottleneck detection module."""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bottleneck import analyze_bottlenecks, save_bottleneck_analysis
from src.utils import load_config, get_project_root


def test_bottlenecks_file_created():
    """Test that bottlenecks.csv is created with expected columns."""
    from src.generate_data import generate_fc_data, save_raw_data
    from src.preprocess import preprocess_data, save_clean_data
    from src.capacity import compute_capacity_metrics, save_capacity_metrics
    
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
    
    # Compute capacity metrics if not exists
    hourly_file = project_root / config['data']['step_hourly_file']
    if not hourly_file.exists():
        metrics = compute_capacity_metrics(config)
        save_capacity_metrics(metrics, config)
    
    # Analyze bottlenecks
    df, summary = analyze_bottlenecks(config)
    save_bottleneck_analysis(df, summary, config)
    
    # Check file exists
    bottlenecks_file = project_root / config['data']['bottlenecks_file']
    assert bottlenecks_file.exists(), "Bottlenecks file should be created"
    
    # Check expected columns
    df_loaded = pd.read_csv(bottlenecks_file)
    expected_columns = ['is_bottleneck', 'bottleneck_step']
    for col in expected_columns:
        assert col in df_loaded.columns, f"Missing column: {col}"

