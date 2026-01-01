"""Bottleneck detection and analysis."""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple

from .utils import load_config, ensure_dir, get_project_root


def load_hourly_metrics(config: Dict[str, Any] = None) -> pd.DataFrame:
    """Load hourly metrics data.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        DataFrame with hourly metrics
    """
    if config is None:
        config = load_config()
    
    project_root = get_project_root()
    hourly_file = project_root / config['data']['step_hourly_file']
    
    if not hourly_file.exists():
        raise FileNotFoundError(f"Hourly metrics file not found: {hourly_file}. Run 'python run.py analyze' first.")
    
    df = pd.read_csv(hourly_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    return df


def detect_bottlenecks(df: pd.DataFrame, threshold_util: float = 0.95) -> pd.DataFrame:
    """Detect bottleneck hours and steps.
    
    A bottleneck is defined as:
    - utilization >= threshold AND (backlog increasing OR throughput_loss > 0)
    
    Args:
        df: Hourly metrics DataFrame
        threshold_util: Utilization threshold
        
    Returns:
        DataFrame with bottleneck flags
    """
    df = df.copy()
    df = df.sort_values(['step', 'timestamp']).reset_index(drop=True)
    
    # Calculate backlog change (increasing = positive)
    df['backlog_change'] = df.groupby('step')['backlog_units'].diff().fillna(0)
    
    # Bottleneck condition
    df['is_bottleneck'] = (
        (df['utilization'] >= threshold_util) &
        ((df['backlog_change'] > 0) | (df['throughput_loss_units'] > 0))
    )
    
    # Identify bottleneck step per hour (step with max utilization or max throughput loss)
    def get_bottleneck_step(group):
        if group['utilization'].max() >= threshold_util:
            return group.loc[group['utilization'].idxmax(), 'step']
        elif group['throughput_loss_units'].max() > 0:
            return group.loc[group['throughput_loss_units'].idxmax(), 'step']
        else:
            return None
    
    hourly_bottleneck = df.groupby('timestamp').apply(get_bottleneck_step).reset_index()
    hourly_bottleneck.columns = ['timestamp', 'bottleneck_step']
    
    df = df.merge(hourly_bottleneck, on='timestamp', how='left')
    
    return df


def summarize_bottlenecks(df: pd.DataFrame) -> Dict[str, Any]:
    """Summarize bottleneck statistics.
    
    Args:
        df: DataFrame with bottleneck flags
        
    Returns:
        Dictionary with summary statistics
    """
    summary = {}
    
    # Total bottleneck hours
    summary['total_bottleneck_hours'] = df['is_bottleneck'].sum()
    
    # Bottleneck hours by step
    summary['bottleneck_hours_by_step'] = df[df['is_bottleneck']].groupby('step').size().to_dict()
    
    # Top 10 worst hours
    worst_hours = df.nlargest(10, 'throughput_loss_units')[
        ['timestamp', 'step', 'utilization', 'throughput_loss_units', 'backlog_units']
    ]
    summary['top_10_worst_hours'] = worst_hours.to_dict('records')
    
    # Bottleneck step distribution
    bottleneck_steps = df[df['is_bottleneck']]['step'].value_counts().to_dict()
    summary['bottleneck_step_distribution'] = bottleneck_steps
    
    return summary


def generate_bottleneck_report(summary: Dict[str, Any], config: Dict[str, Any] = None) -> str:
    """Generate markdown report for bottlenecks.
    
    Args:
        summary: Summary dictionary
        config: Configuration dictionary
        
    Returns:
        Markdown report string
    """
    report = "# Bottleneck Analysis Summary\n\n"
    
    report += "## Overview\n\n"
    report += f"**Total Bottleneck Hours:** {summary['total_bottleneck_hours']}\n\n"
    
    report += "## Bottleneck Hours by Step\n\n"
    if summary['bottleneck_hours_by_step']:
        for step, count in summary['bottleneck_hours_by_step'].items():
            report += f"- **{step}**: {count} hours\n"
    else:
        report += "No bottlenecks detected.\n"
    report += "\n"
    
    report += "## Top 10 Worst Hours (by Throughput Loss)\n\n"
    report += "| Timestamp | Step | Utilization | Throughput Loss (units) | Backlog (units) |\n"
    report += "|-----------|------|-------------|------------------------|-----------------|\n"
    
    for hour in summary['top_10_worst_hours']:
        report += f"| {hour['timestamp']} | {hour['step']} | {hour['utilization']:.2%} | {hour['throughput_loss_units']:.0f} | {hour['backlog_units']:.0f} |\n"
    
    report += "\n## Bottleneck Step Distribution\n\n"
    if summary['bottleneck_step_distribution']:
        for step, count in sorted(summary['bottleneck_step_distribution'].items(), key=lambda x: x[1], reverse=True):
            report += f"- **{step}**: {count} bottleneck occurrences\n"
    else:
        report += "No bottlenecks detected.\n"
    
    return report


def analyze_bottlenecks(config: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Main function to analyze bottlenecks.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (bottleneck DataFrame, summary dictionary)
    """
    if config is None:
        config = load_config()
    
    print("Loading hourly metrics...")
    df = load_hourly_metrics(config)
    
    print("Detecting bottlenecks...")
    threshold = config['bottleneck_threshold_util']
    df = detect_bottlenecks(df, threshold)
    
    print("Summarizing bottlenecks...")
    summary = summarize_bottlenecks(df)
    
    return df, summary


def save_bottleneck_analysis(
    df: pd.DataFrame,
    summary: Dict[str, Any],
    config: Dict[str, Any] = None
) -> Dict[str, Path]:
    """Save bottleneck analysis results.
    
    Args:
        df: Bottleneck DataFrame
        summary: Summary dictionary
        config: Configuration dictionary
        
    Returns:
        Dictionary of saved file paths
    """
    if config is None:
        config = load_config()
    
    project_root = get_project_root()
    
    # Save bottleneck data
    bottlenecks_file = project_root / config['data']['bottlenecks_file']
    ensure_dir(bottlenecks_file.parent)
    df.to_csv(bottlenecks_file, index=False)
    print(f"Saved bottleneck data to: {bottlenecks_file}")
    
    # Save summary report
    summary_file = project_root / config['reports']['bottleneck_summary']
    ensure_dir(summary_file.parent)
    report = generate_bottleneck_report(summary, config)
    with open(summary_file, 'w') as f:
        f.write(report)
    print(f"Saved bottleneck summary to: {summary_file}")
    
    return {
        'bottlenecks': bottlenecks_file,
        'summary': summary_file
    }


def main():
    """Main entry point for bottleneck analysis."""
    config = load_config()
    df, summary = analyze_bottlenecks(config)
    save_bottleneck_analysis(df, summary, config)


if __name__ == "__main__":
    main()

