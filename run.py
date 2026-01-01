"""Main runner script for FC capacity planning pipeline."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils import load_config
from src.generate_data import generate_fc_data, save_raw_data
from src.preprocess import preprocess_data, save_clean_data
from src.capacity import compute_capacity_metrics, save_capacity_metrics
from src.bottleneck import analyze_bottlenecks, save_bottleneck_analysis
from src.recommendations import analyze_staffing, save_staffing_analysis
from src.kpis import generate_kpis, save_kpis


def run_generate():
    """Generate synthetic data."""
    print("\n" + "="*60)
    print("STEP 1: Generating Synthetic Data")
    print("="*60)
    config = load_config()
    df = generate_fc_data(config)
    save_raw_data(df, config=config)
    print("[OK] Data generation complete\n")


def run_preprocess():
    """Preprocess raw data."""
    print("\n" + "="*60)
    print("STEP 2: Preprocessing Data")
    print("="*60)
    config = load_config()
    df = preprocess_data(config)
    save_clean_data(df, config)
    print("[OK] Preprocessing complete\n")


def run_analyze():
    """Run capacity analytics."""
    print("\n" + "="*60)
    print("STEP 3: Computing Capacity Metrics")
    print("="*60)
    config = load_config()
    metrics = compute_capacity_metrics(config)
    save_capacity_metrics(metrics, config)
    print("[OK] Capacity analytics complete\n")


def run_bottlenecks():
    """Run bottleneck analysis."""
    print("\n" + "="*60)
    print("STEP 4: Analyzing Bottlenecks")
    print("="*60)
    config = load_config()
    df, summary = analyze_bottlenecks(config)
    save_bottleneck_analysis(df, summary, config)
    print("[OK] Bottleneck analysis complete\n")


def run_recommend():
    """Run staffing recommendations."""
    print("\n" + "="*60)
    print("STEP 5: Computing Staffing Recommendations")
    print("="*60)
    config = load_config()
    df, summary = analyze_staffing(config)
    save_staffing_analysis(df, summary, config)
    print("[OK] Staffing recommendations complete\n")


def run_report():
    """Generate KPI reports."""
    print("\n" + "="*60)
    print("STEP 6: Generating KPI Reports")
    print("="*60)
    config = load_config()
    kpis = generate_kpis(config)
    save_kpis(kpis, config)
    print("[OK] KPI reports complete\n")


def run_app():
    """Launch Streamlit app."""
    print("\n" + "="*60)
    print("Launching Streamlit Dashboard")
    print("="*60)
    import subprocess
    import os
    
    app_path = project_root / "app" / "streamlit_app.py"
    os.chdir(project_root)
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])


def run_all():
    """Run all pipeline steps in order."""
    print("\n" + "="*60)
    print("FC CAPACITY PLANNING PIPELINE")
    print("="*60)
    
    try:
        run_generate()
        run_preprocess()
        run_analyze()
        run_bottlenecks()
        run_recommend()
        run_report()
        
        print("\n" + "="*60)
        print("[OK] PIPELINE COMPLETE")
        print("="*60)
        print("\nGenerated files:")
        config = load_config()
        print(f"  - Raw data: {config['data']['raw_file']}")
        print(f"  - Processed data: {config['data']['processed_file']}")
        print(f"  - Hourly metrics: {config['data']['step_hourly_file']}")
        print(f"  - Daily metrics: {config['data']['step_daily_file']}")
        print(f"  - Site metrics: {config['data']['site_daily_file']}")
        print(f"  - Bottlenecks: {config['data']['bottlenecks_file']}")
        print(f"  - Staffing: {config['data']['staffing_file']}")
        print(f"  - Reports: {config['reports']['kpis_md']}")
        print("\nTo view dashboard, run: python run.py app\n")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        # Default to 'all' if no argument provided
        command = 'all'
    else:
        command = sys.argv[1].lower()
    
    commands = {
        'generate': run_generate,
        'preprocess': run_preprocess,
        'analyze': run_analyze,
        'bottlenecks': run_bottlenecks,
        'recommend': run_recommend,
        'report': run_report,
        'app': run_app,
        'all': run_all
    }
    
    if command not in commands:
        print(f"Unknown command: {command}")
        print("\nAvailable commands:")
        for cmd in commands.keys():
            print(f"  python run.py {cmd}")
        sys.exit(1)
    
    commands[command]()


if __name__ == "__main__":
    main()

