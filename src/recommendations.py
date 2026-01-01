"""Staffing recommendations based on service targets."""

import pandas as pd
import numpy as np
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


def compute_staffing_recommendations(
    df: pd.DataFrame,
    service_target: float,
    uph_by_step: Dict[str, float],
    wage_per_hour: float
) -> pd.DataFrame:
    """Compute recommended headcount to meet service targets.
    
    Args:
        df: Hourly metrics DataFrame
        service_target: Target service level (fraction)
        uph_by_step: Units per hour by step
        wage_per_hour: Wage per hour
        
    Returns:
        DataFrame with recommendations
    """
    df = df.copy()
    
    # Calculate required units to meet service target
    # Approximate backlog_in (previous hour's backlog)
    df = df.sort_values(['step', 'timestamp']).reset_index(drop=True)
    df['backlog_in'] = df.groupby('step')['backlog_units'].shift(1).fillna(0)
    
    # Required units = demand + backlog
    df['required_units'] = df['demand_units'] + df['backlog_in']
    
    # Required capacity to meet service target
    df['required_capacity_units'] = df['required_units'] / service_target
    
    # Required labor hours
    df['uph'] = df['step'].map(uph_by_step)
    df['required_labor_hours'] = df['required_capacity_units'] / (df['uph'] + 1e-6)
    
    # Recommended headcount (ceiling)
    df['recommended_headcount'] = np.ceil(df['required_labor_hours']).astype(int)
    
    # Headcount gap
    df['headcount_gap'] = df['recommended_headcount'] - df['headcount_used']
    
    # Labor cost impact (only for additional headcount needed)
    df['labor_cost_impact'] = np.maximum(0, df['headcount_gap']) * wage_per_hour
    
    return df


def summarize_staffing(df: pd.DataFrame) -> Dict[str, Any]:
    """Summarize staffing recommendations.
    
    Args:
        df: DataFrame with recommendations
        
    Returns:
        Dictionary with summary statistics
    """
    summary = {}
    
    # Total headcount gap
    summary['total_headcount_gap_hours'] = df['headcount_gap'].sum()
    summary['total_positive_gap_hours'] = df[df['headcount_gap'] > 0]['headcount_gap'].sum()
    
    # Total cost impact
    summary['total_cost_impact'] = df['labor_cost_impact'].sum()
    
    # Top gaps by step
    summary['headcount_gap_by_step'] = df.groupby('step')['headcount_gap'].sum().to_dict()
    
    # Top 20 hours with largest gaps
    top_gaps = df.nlargest(20, 'headcount_gap')[
        ['timestamp', 'step', 'headcount_used', 'recommended_headcount', 
         'headcount_gap', 'labor_cost_impact', 'utilization']
    ]
    summary['top_20_gaps'] = top_gaps.to_dict('records')
    
    # Average gap by step
    summary['avg_gap_by_step'] = df.groupby('step')['headcount_gap'].mean().to_dict()
    
    return summary


def generate_staffing_report(summary: Dict[str, Any], config: Dict[str, Any] = None) -> str:
    """Generate markdown report for staffing recommendations.
    
    Args:
        summary: Summary dictionary
        config: Configuration dictionary
        
    Returns:
        Markdown report string
    """
    report = "# Staffing Recommendations Summary\n\n"
    
    report += "## Overview\n\n"
    report += f"**Total Headcount Gap (hours):** {summary['total_headcount_gap_hours']:.0f}\n\n"
    report += f"**Total Positive Gap (hours):** {summary['total_positive_gap_hours']:.0f}\n\n"
    report += f"**Estimated Additional Labor Cost:** ${summary['total_cost_impact']:,.2f}\n\n"
    
    report += "## Headcount Gap by Step\n\n"
    report += "| Step | Total Gap (hours) | Average Gap |\n"
    report += "|------|-------------------|-------------|\n"
    for step in sorted(summary['headcount_gap_by_step'].keys()):
        total_gap = summary['headcount_gap_by_step'][step]
        avg_gap = summary['avg_gap_by_step'].get(step, 0)
        report += f"| {step} | {total_gap:.0f} | {avg_gap:.2f} |\n"
    report += "\n"
    
    report += "## Top 20 Hours with Largest Headcount Gaps\n\n"
    report += "| Timestamp | Step | Current | Recommended | Gap | Cost Impact | Utilization |\n"
    report += "|-----------|------|---------|-------------|-----|-------------|-------------|\n"
    
    for hour in summary['top_20_gaps']:
        report += f"| {hour['timestamp']} | {hour['step']} | {hour['headcount_used']} | {hour['recommended_headcount']} | {hour['headcount_gap']} | ${hour['labor_cost_impact']:.2f} | {hour['utilization']:.2%} |\n"
    
    report += "\n## Recommendations\n\n"
    report += "1. **Prioritize steps with largest gaps**: Focus staffing increases on steps showing consistent headcount gaps.\n"
    report += "2. **Peak hour coverage**: Ensure adequate staffing during peak hours identified in top gaps.\n"
    report += "3. **Cross-training**: Consider cross-training associates to enable flexible reallocation across steps.\n"
    report += "4. **Capacity planning**: Review capacity constraints that may require equipment or process improvements beyond staffing.\n"
    
    return report


def analyze_staffing(config: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Main function to analyze staffing needs.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (recommendations DataFrame, summary dictionary)
    """
    if config is None:
        config = load_config()
    
    print("Loading hourly metrics...")
    df = load_hourly_metrics(config)
    
    print("Computing staffing recommendations...")
    df = compute_staffing_recommendations(
        df,
        service_target=config['service_target'],
        uph_by_step=config['uph_by_step'],
        wage_per_hour=config['wage_per_hour']
    )
    
    print("Summarizing staffing recommendations...")
    summary = summarize_staffing(df)
    
    return df, summary


def save_staffing_analysis(
    df: pd.DataFrame,
    summary: Dict[str, Any],
    config: Dict[str, Any] = None
) -> Dict[str, Path]:
    """Save staffing analysis results.
    
    Args:
        df: Recommendations DataFrame
        summary: Summary dictionary
        config: Configuration dictionary
        
    Returns:
        Dictionary of saved file paths
    """
    if config is None:
        config = load_config()
    
    project_root = get_project_root()
    
    # Save recommendations
    staffing_file = project_root / config['data']['staffing_file']
    ensure_dir(staffing_file.parent)
    df.to_csv(staffing_file, index=False)
    print(f"Saved staffing recommendations to: {staffing_file}")
    
    # Save summary report
    summary_file = project_root / config['reports']['staffing_summary']
    ensure_dir(summary_file.parent)
    report = generate_staffing_report(summary, config)
    with open(summary_file, 'w') as f:
        f.write(report)
    print(f"Saved staffing summary to: {summary_file}")
    
    return {
        'staffing': staffing_file,
        'summary': summary_file
    }


def main():
    """Main entry point for staffing analysis."""
    config = load_config()
    df, summary = analyze_staffing(config)
    save_staffing_analysis(df, summary, config)


if __name__ == "__main__":
    main()

