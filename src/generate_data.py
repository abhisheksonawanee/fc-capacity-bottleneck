"""Generate synthetic fulfillment center hourly operations data."""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
import sys

from .utils import load_config, ensure_dir, get_project_root


def generate_hourly_demand(
    start_date: str,
    num_days: int,
    base_demand_mean: float,
    hourly_seasonality: Dict[str, Any],
    day_of_week: Dict[str, float],
    promo_days: int,
    promo_multiplier: float,
    random_state: int
) -> pd.DataFrame:
    """Generate hourly demand with seasonality and promotions.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        num_days: Number of days to generate
        base_demand_mean: Base daily demand mean
        hourly_seasonality: Hourly seasonality config
        day_of_week: Day of week multipliers
        promo_days: Number of promo days
        promo_multiplier: Multiplier for promo days
        random_state: Random seed
        
    Returns:
        DataFrame with timestamp and demand_units
    """
    np.random.seed(random_state)
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    hours = []
    timestamps = []
    
    # Generate promo days
    promo_day_indices = np.random.choice(num_days, size=promo_days, replace=False)
    promo_dates = {start + timedelta(days=int(d)) for d in promo_day_indices}
    
    for day in range(num_days):
        current_date = start + timedelta(days=day)
        is_weekend = current_date.weekday() >= 5
        is_promo = current_date.date() in {d.date() for d in promo_dates}
        
        dow_multiplier = day_of_week["weekend_multiplier"] if is_weekend else day_of_week["weekday_multiplier"]
        promo_mult = promo_multiplier if is_promo else 1.0
        
        for hour in range(24):
            timestamp = current_date + timedelta(hours=hour)
            timestamps.append(timestamp)
            
            # Hourly seasonality
            if hour in hourly_seasonality["peak_hours"]:
                hour_mult = hourly_seasonality["peak_multiplier"]
            else:
                hour_mult = hourly_seasonality["off_peak_multiplier"]
            
            # Base demand with noise
            hourly_demand = (base_demand_mean / 24) * dow_multiplier * hour_mult * promo_mult
            # Add noise (10% coefficient of variation)
            noise = np.random.normal(1.0, 0.1)
            hourly_demand = max(0, hourly_demand * noise)
            
            hours.append(hourly_demand)
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'demand_units': hours
    })


def generate_step_data(
    demand_df: pd.DataFrame,
    step: str,
    step_capacity_base: float,
    capacity_variability_std: float,
    downtime_probability: float,
    downtime_severity: float,
    uph: float,
    cycle_time_base: float,
    congestion_multiplier_max: float,
    random_state: int
) -> pd.DataFrame:
    """Generate operational data for a single step.
    
    Args:
        demand_df: DataFrame with timestamp and demand_units
        step: Step name
        step_capacity_base: Base capacity multiplier for this step
        capacity_variability_std: Standard deviation for capacity variability
        downtime_probability: Probability of capacity drop
        downtime_severity: Severity of capacity drop (fraction)
        uph: Units per hour for this step
        cycle_time_base: Base cycle time in minutes
        congestion_multiplier_max: Max cycle time multiplier
        random_state: Random seed
        
    Returns:
        DataFrame with step operational data
    """
    np.random.seed(random_state + hash(step) % 1000)
    
    df = demand_df.copy()
    df['step'] = step
    
    # Adjust demand for step (receive leads, others follow with some lag/backlog)
    if step == 'receive':
        step_demand = df['demand_units'].values
    else:
        # Other steps have demand from previous step's processed units (simplified)
        # For realism, add some lag and variability
        lag = 1 if step == 'pick' else (2 if step == 'pack' else 3)
        step_demand = df['demand_units'].values * (1 - 0.05 * lag)  # Slight reduction with lag
        step_demand = np.maximum(0, step_demand + np.random.normal(0, step_demand * 0.05))
    
    # Generate capacity
    base_capacity = step_demand.mean() * step_capacity_base
    capacity_units = base_capacity * (1 + np.random.normal(0, capacity_variability_std, len(df)))
    
    # Apply downtime
    downtime_mask = np.random.random(len(df)) < downtime_probability
    capacity_units[downtime_mask] *= (1 - downtime_severity)
    capacity_units = np.maximum(0, capacity_units)
    
    # Initialize backlog tracking
    backlog_units = np.zeros(len(df))
    processed_units = np.zeros(len(df))
    
    # Process hour by hour
    for i in range(len(df)):
        demand_in = step_demand[i]
        backlog_in = backlog_units[i-1] if i > 0 else 0
        total_demand = demand_in + backlog_in
        
        # Process what we can
        processed = min(total_demand, capacity_units[i])
        processed_units[i] = processed
        
        # Update backlog
        backlog_units[i] = max(0, total_demand - processed)
    
    # Calculate utilization
    utilization = np.clip(processed_units / (capacity_units + 1e-6), 0, 1)
    
    # Calculate cycle time (base * congestion factor)
    congestion_factor = 1.0 + (utilization - 0.7) * (congestion_multiplier_max - 1.0) / 0.3
    congestion_factor = np.clip(congestion_factor, 1.0, congestion_multiplier_max)
    cycle_time_min = cycle_time_base * congestion_factor
    
    # Calculate labor metrics
    labor_hours_used = processed_units / (uph + 1e-6)
    headcount_used = np.ceil(labor_hours_used).astype(int)
    
    df['demand_units'] = step_demand
    df['capacity_units'] = capacity_units
    df['processed_units'] = processed_units
    df['backlog_units'] = backlog_units
    df['utilization'] = utilization
    df['cycle_time_min'] = cycle_time_min
    df['uph'] = uph
    df['labor_hours_used'] = labor_hours_used
    df['headcount_used'] = headcount_used
    
    return df


def generate_fc_data(config: Dict[str, Any] = None) -> pd.DataFrame:
    """Generate complete FC hourly operations dataset.
    
    Args:
        config: Configuration dictionary (if None, loads from file)
        
    Returns:
        DataFrame with all operational data
    """
    if config is None:
        config = load_config()
    
    project_root = get_project_root()
    
    # Extract parameters
    start_date = config['start_date']
    num_days = config['num_days']
    random_state = config['random_state']
    steps = config['steps']
    
    # Generate base demand
    print(f"Generating demand data for {num_days} days starting {start_date}...")
    demand_df = generate_hourly_demand(
        start_date=start_date,
        num_days=num_days,
        base_demand_mean=config['demand']['base_demand_mean'],
        hourly_seasonality=config['demand']['hourly_seasonality'],
        day_of_week=config['demand']['day_of_week'],
        promo_days=config['demand']['promo_days'],
        promo_multiplier=config['demand']['promo_multiplier'],
        random_state=random_state
    )
    
    # Generate data for each step
    all_data = []
    for step in steps:
        print(f"Generating data for step: {step}...")
        step_df = generate_step_data(
            demand_df=demand_df,
            step=step,
            step_capacity_base=config['capacity']['step_capacity_base'][step],
            capacity_variability_std=config['capacity']['variability_std'],
            downtime_probability=config['capacity']['downtime_probability'],
            downtime_severity=config['capacity']['downtime_severity'],
            uph=config['uph_by_step'][step],
            cycle_time_base=config['cycle_time']['base_min'][step],
            congestion_multiplier_max=config['cycle_time']['congestion_multiplier_max'],
            random_state=random_state
        )
        all_data.append(step_df)
    
    # Combine all steps
    result_df = pd.concat(all_data, ignore_index=True)
    
    # Sort by timestamp and step
    result_df = result_df.sort_values(['timestamp', 'step']).reset_index(drop=True)
    
    return result_df


def save_raw_data(df: pd.DataFrame, output_path: str = None, config: Dict[str, Any] = None) -> Path:
    """Save generated data to CSV.
    
    Args:
        df: DataFrame to save
        output_path: Output file path (if None, uses config)
        config: Configuration dictionary
        
    Returns:
        Path to saved file
    """
    if config is None:
        config = load_config()
    
    project_root = get_project_root()
    
    if output_path is None:
        output_path = config['data']['raw_file']
    
    output_file = project_root / output_path
    ensure_dir(output_file.parent)
    
    df.to_csv(output_file, index=False)
    print(f"Saved raw data to: {output_file}")
    print(f"Shape: {df.shape}")
    
    return output_file


def main():
    """Main entry point for data generation."""
    config = load_config()
    df = generate_fc_data(config)
    save_raw_data(df, config=config)


if __name__ == "__main__":
    main()

