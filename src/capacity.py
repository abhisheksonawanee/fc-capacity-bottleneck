"""Capacity analytics and metrics computation."""

import pandas as pd
from pathlib import Path
from typing import Dict, Any

from .utils import load_config, ensure_dir, get_project_root


def load_clean_data(config: Dict[str, Any] = None) -> pd.DataFrame:
    """Load preprocessed data.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        DataFrame with clean data
    """
    if config is None:
        config = load_config()
    
    project_root = get_project_root()
    processed_file = project_root / config['data']['processed_file']
    
    if not processed_file.exists():
        raise FileNotFoundError(f"Processed data file not found: {processed_file}. Run 'python run.py preprocess' first.")
    
    df = pd.read_csv(processed_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = pd.to_datetime(df['date'])
    
    return df


def compute_utilization(df: pd.DataFrame) -> pd.DataFrame:
    """Compute utilization metrics.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with utilization computed
    """
    df = df.copy()
    
    # Utilization should already be in data, but recalculate to ensure accuracy
    df['utilization'] = (df['processed_units'] / (df['capacity_units'] + 1e-6)).clip(0, 1)
    
    return df


def compute_service_level(df: pd.DataFrame) -> pd.DataFrame:
    """Compute service level metrics.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with service level computed
    """
    df = df.copy()
    
    # Approximate backlog_in for service level calculation
    # For each step, backlog_in is previous hour's backlog_out
    df = df.sort_values(['step', 'timestamp']).reset_index(drop=True)
    
    # Calculate backlog_in (previous hour's backlog)
    df['backlog_in'] = df.groupby('step')['backlog_units'].shift(1).fillna(0)
    
    # Total demand = current demand + incoming backlog
    df['total_demand'] = df['demand_units'] + df['backlog_in']
    
    # Service level = processed / total_demand
    df['service_level_hourly'] = (df['processed_units'] / (df['total_demand'] + 1e-6).clip(0, 1))
    
    # Throughput loss
    df['throughput_loss_units'] = (df['total_demand'] - df['processed_units']).clip(0, None)
    
    return df


def aggregate_hourly_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate metrics by hour and step.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Aggregated hourly metrics
    """
    hourly = df.groupby(['timestamp', 'step']).agg({
        'demand_units': 'sum',
        'capacity_units': 'sum',
        'processed_units': 'sum',
        'backlog_units': 'mean',  # Use mean to get end-of-hour backlog
        'utilization': 'mean',
        'cycle_time_min': 'mean',
        'service_level_hourly': 'mean',
        'throughput_loss_units': 'sum',
        'labor_hours_used': 'sum',
        'headcount_used': 'sum'
    }).reset_index()
    
    return hourly


def aggregate_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate metrics by day and step.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Aggregated daily metrics by step
    """
    daily_step = df.groupby(['date', 'step']).agg({
        'demand_units': 'sum',
        'capacity_units': 'sum',
        'processed_units': 'sum',
        'backlog_units': 'mean',  # Average backlog over day
        'utilization': 'mean',
        'cycle_time_min': 'mean',
        'service_level_hourly': 'mean',
        'throughput_loss_units': 'sum',
        'labor_hours_used': 'sum',
        'headcount_used': 'sum'
    }).reset_index()
    
    return daily_step


def aggregate_site_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate metrics by day across all steps.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Aggregated daily site metrics
    """
    daily_site = df.groupby('date').agg({
        'demand_units': 'sum',
        'capacity_units': 'sum',
        'processed_units': 'sum',
        'backlog_units': 'mean',
        'utilization': 'mean',
        'cycle_time_min': 'mean',
        'service_level_hourly': 'mean',
        'throughput_loss_units': 'sum',
        'labor_hours_used': 'sum',
        'headcount_used': 'sum'
    }).reset_index()
    
    return daily_site


def compute_capacity_metrics(config: Dict[str, Any] = None) -> Dict[str, pd.DataFrame]:
    """Main function to compute all capacity metrics.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary with all metric DataFrames
    """
    if config is None:
        config = load_config()
    
    print("Loading clean data...")
    df = load_clean_data(config)
    
    print("Computing utilization...")
    df = compute_utilization(df)
    
    print("Computing service level...")
    df = compute_service_level(df)
    
    print("Aggregating hourly metrics...")
    hourly_metrics = aggregate_hourly_metrics(df)
    
    print("Aggregating daily metrics by step...")
    daily_step_metrics = aggregate_daily_metrics(df)
    
    print("Aggregating site daily metrics...")
    site_daily_metrics = aggregate_site_daily_metrics(df)
    
    return {
        'hourly': hourly_metrics,
        'daily_step': daily_step_metrics,
        'site_daily': site_daily_metrics
    }


def save_capacity_metrics(metrics: Dict[str, pd.DataFrame], config: Dict[str, Any] = None) -> Dict[str, Path]:
    """Save capacity metrics to CSV files.
    
    Args:
        metrics: Dictionary of metric DataFrames
        config: Configuration dictionary
        
    Returns:
        Dictionary of saved file paths
    """
    if config is None:
        config = load_config()
    
    project_root = get_project_root()
    
    output_files = {}
    
    # Save hourly metrics
    hourly_file = project_root / config['data']['step_hourly_file']
    ensure_dir(hourly_file.parent)
    metrics['hourly'].to_csv(hourly_file, index=False)
    print(f"Saved hourly metrics to: {hourly_file}")
    output_files['hourly'] = hourly_file
    
    # Save daily step metrics
    daily_step_file = project_root / config['data']['step_daily_file']
    ensure_dir(daily_step_file.parent)
    metrics['daily_step'].to_csv(daily_step_file, index=False)
    print(f"Saved daily step metrics to: {daily_step_file}")
    output_files['daily_step'] = daily_step_file
    
    # Save site daily metrics
    site_daily_file = project_root / config['data']['site_daily_file']
    ensure_dir(site_daily_file.parent)
    metrics['site_daily'].to_csv(site_daily_file, index=False)
    print(f"Saved site daily metrics to: {site_daily_file}")
    output_files['site_daily'] = site_daily_file
    
    return output_files


def main():
    """Main entry point for capacity analytics."""
    config = load_config()
    metrics = compute_capacity_metrics(config)
    save_capacity_metrics(metrics, config)


if __name__ == "__main__":
    main()

