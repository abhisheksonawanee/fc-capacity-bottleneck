"""KPI computation and reporting."""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any

from .utils import load_config, ensure_dir, get_project_root


def load_all_data(config: Dict[str, Any] = None) -> Dict[str, pd.DataFrame]:
    """Load all processed data files.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary of DataFrames
    """
    if config is None:
        config = load_config()
    
    project_root = get_project_root()
    
    data = {}
    
    # Load site daily metrics
    site_daily_file = project_root / config['data']['site_daily_file']
    if site_daily_file.exists():
        data['site_daily'] = pd.read_csv(site_daily_file)
        data['site_daily']['date'] = pd.to_datetime(data['site_daily']['date'])
    
    # Load step daily metrics
    step_daily_file = project_root / config['data']['step_daily_file']
    if step_daily_file.exists():
        data['step_daily'] = pd.read_csv(step_daily_file)
        data['step_daily']['date'] = pd.to_datetime(data['step_daily']['date'])
    
    # Load bottlenecks
    bottlenecks_file = project_root / config['data']['bottlenecks_file']
    if bottlenecks_file.exists():
        data['bottlenecks'] = pd.read_csv(bottlenecks_file)
        data['bottlenecks']['timestamp'] = pd.to_datetime(data['bottlenecks']['timestamp'])
    
    # Load staffing recommendations
    staffing_file = project_root / config['data']['staffing_file']
    if staffing_file.exists():
        data['staffing'] = pd.read_csv(staffing_file)
        data['staffing']['timestamp'] = pd.to_datetime(data['staffing']['timestamp'])
    
    return data


def compute_kpis(data: Dict[str, pd.DataFrame], config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Compute key performance indicators.
    
    Args:
        data: Dictionary of DataFrames
        config: Configuration dictionary
        
    Returns:
        Dictionary of KPIs
    """
    kpis = {}
    
    if 'step_daily' in data:
        df = data['step_daily']
        
        # Average utilization by step
        kpis['avg_utilization_by_step'] = df.groupby('step')['utilization'].mean().to_dict()
        
        # Total throughput processed
        kpis['total_throughput_processed'] = df['processed_units'].sum()
        
        # Total throughput loss
        kpis['total_throughput_loss'] = df['throughput_loss_units'].sum()
        
        # Average cycle time by step
        kpis['avg_cycle_time_by_step'] = df.groupby('step')['cycle_time_min'].mean().to_dict()
        
        # P90 cycle time by step
        kpis['p90_cycle_time_by_step'] = df.groupby('step')['cycle_time_min'].quantile(0.90).to_dict()
    
    if 'bottlenecks' in data:
        df = data['bottlenecks']
        
        # Bottleneck share by step
        bottleneck_steps = df[df['is_bottleneck']]['step'].value_counts()
        total_bottlenecks = bottleneck_steps.sum()
        if total_bottlenecks > 0:
            kpis['bottleneck_share_by_step'] = (bottleneck_steps / total_bottlenecks * 100).to_dict()
        else:
            kpis['bottleneck_share_by_step'] = {}
    
    if 'staffing' in data:
        df = data['staffing']
        
        # Extra headcount hours needed
        positive_gaps = df[df['headcount_gap'] > 0]
        kpis['extra_headcount_hours_needed'] = positive_gaps['headcount_gap'].sum()
        
        # Estimated cost to hit service target
        kpis['estimated_cost_to_hit_target'] = positive_gaps['labor_cost_impact'].sum()
    
    if 'site_daily' in data:
        df = data['site_daily']
        
        # Overall average utilization
        kpis['overall_avg_utilization'] = df['utilization'].mean()
        
        # Overall average service level
        kpis['overall_avg_service_level'] = df['service_level_hourly'].mean()
        
        # Total days analyzed
        kpis['total_days'] = len(df)
    
    return kpis


def generate_kpi_report(kpis: Dict[str, Any], config: Dict[str, Any] = None) -> str:
    """Generate markdown report for KPIs.
    
    Args:
        kpis: KPI dictionary
        config: Configuration dictionary
        
    Returns:
        Markdown report string
    """
    report = "# Key Performance Indicators\n\n"
    
    report += "## Overview Metrics\n\n"
    if 'total_days' in kpis:
        report += f"- **Analysis Period:** {kpis['total_days']} days\n"
    if 'overall_avg_utilization' in kpis:
        report += f"- **Overall Average Utilization:** {kpis['overall_avg_utilization']:.2%}\n"
    if 'overall_avg_service_level' in kpis:
        report += f"- **Overall Average Service Level:** {kpis['overall_avg_service_level']:.2%}\n"
    report += "\n"
    
    report += "## Throughput Metrics\n\n"
    if 'total_throughput_processed' in kpis:
        report += f"- **Total Throughput Processed:** {kpis['total_throughput_processed']:,.0f} units\n"
    if 'total_throughput_loss' in kpis:
        report += f"- **Total Throughput Loss:** {kpis['total_throughput_loss']:,.0f} units\n"
    report += "\n"
    
    report += "## Utilization by Step\n\n"
    if 'avg_utilization_by_step' in kpis:
        report += "| Step | Average Utilization |\n"
        report += "|------|---------------------|\n"
        for step, util in sorted(kpis['avg_utilization_by_step'].items()):
            report += f"| {step} | {util:.2%} |\n"
        report += "\n"
    
    report += "## Cycle Time Metrics\n\n"
    if 'avg_cycle_time_by_step' in kpis:
        report += "| Step | Average Cycle Time (min) | P90 Cycle Time (min) |\n"
        report += "|------|-------------------------|----------------------|\n"
        for step in sorted(kpis['avg_cycle_time_by_step'].keys()):
            avg = kpis['avg_cycle_time_by_step'][step]
            p90 = kpis.get('p90_cycle_time_by_step', {}).get(step, 0)
            report += f"| {step} | {avg:.1f} | {p90:.1f} |\n"
        report += "\n"
    
    report += "## Bottleneck Analysis\n\n"
    if 'bottleneck_share_by_step' in kpis and kpis['bottleneck_share_by_step']:
        report += "| Step | Bottleneck Share (%) |\n"
        report += "|------|---------------------|\n"
        for step, share in sorted(kpis['bottleneck_share_by_step'].items(), key=lambda x: x[1], reverse=True):
            report += f"| {step} | {share:.1f}% |\n"
        report += "\n"
    else:
        report += "No bottlenecks detected.\n\n"
    
    report += "## Staffing Recommendations\n\n"
    if 'extra_headcount_hours_needed' in kpis:
        report += f"- **Extra Headcount Hours Needed:** {kpis['extra_headcount_hours_needed']:,.0f} hours\n"
    if 'estimated_cost_to_hit_target' in kpis:
        report += f"- **Estimated Cost to Hit Service Target:** ${kpis['estimated_cost_to_hit_target']:,.2f}\n"
    report += "\n"
    
    return report


def generate_kpis(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Main function to generate KPIs.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary of KPIs
    """
    if config is None:
        config = load_config()
    
    print("Loading all data...")
    data = load_all_data(config)
    
    print("Computing KPIs...")
    kpis = compute_kpis(data, config)
    
    return kpis


def save_kpis(kpis: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Path]:
    """Save KPI results.
    
    Args:
        kpis: KPI dictionary
        config: Configuration dictionary
        
    Returns:
        Dictionary of saved file paths
    """
    if config is None:
        config = load_config()
    
    project_root = get_project_root()
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_types(obj):
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
            return str(obj)
        elif hasattr(obj, 'item'):  # numpy scalar
            return obj.item()
        elif isinstance(obj, (list, tuple)):
            return [convert_types(x) for x in obj]
        else:
            return obj
    
    kpis_serializable = convert_types(kpis)
    
    # Save JSON
    kpis_json_file = project_root / config['reports']['kpis_json']
    ensure_dir(kpis_json_file.parent)
    with open(kpis_json_file, 'w') as f:
        json.dump(kpis_serializable, f, indent=2)
    print(f"Saved KPIs JSON to: {kpis_json_file}")
    
    # Save markdown report
    kpis_md_file = project_root / config['reports']['kpis_md']
    ensure_dir(kpis_md_file.parent)
    report = generate_kpi_report(kpis, config)
    with open(kpis_md_file, 'w') as f:
        f.write(report)
    print(f"Saved KPIs report to: {kpis_md_file}")
    
    return {
        'json': kpis_json_file,
        'md': kpis_md_file
    }


def main():
    """Main entry point for KPI generation."""
    config = load_config()
    kpis = generate_kpis(config)
    save_kpis(kpis, config)


if __name__ == "__main__":
    main()

