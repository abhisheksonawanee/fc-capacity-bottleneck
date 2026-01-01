"""Streamlit dashboard for FC capacity planning and bottleneck analysis."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import load_config, get_project_root


def load_data_file(file_path: Path) -> pd.DataFrame:
    """Load a data file if it exists.
    
    Args:
        file_path: Path to file
        
    Returns:
        DataFrame or None if file doesn't exist
    """
    if file_path.exists():
        df = pd.read_csv(file_path)
        # Convert date/timestamp columns
        for col in ['date', 'timestamp']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        return df
    return None


def check_data_files(config):
    """Check if required data files exist."""
    project_root = get_project_root()
    required_files = [
        config['data']['site_daily_file'],
        config['data']['step_daily_file'],
        config['data']['bottlenecks_file'],
        config['data']['staffing_file']
    ]
    
    missing = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing.append(file_path)
    
    return missing


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="FC Capacity Planning Dashboard",
        page_icon="📦",
        layout="wide"
    )
    
    st.title("📦 Fulfillment Center Capacity Planning & Bottleneck Analysis")
    st.markdown("---")
    
    # Load config
    try:
        config = load_config()
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        st.stop()
    
    # Check if data files exist
    missing_files = check_data_files(config)
    if missing_files:
        st.warning("⚠️ Required data files are missing. Please run the pipeline first:")
        st.code("python run.py all", language="bash")
        st.markdown("### Missing files:")
        for f in missing_files:
            st.write(f"- `{f}`")
        st.stop()
    
    project_root = get_project_root()
    
    # Load data
    site_daily = load_data_file(project_root / config['data']['site_daily_file'])
    step_daily = load_data_file(project_root / config['data']['step_daily_file'])
    bottlenecks = load_data_file(project_root / config['data']['bottlenecks_file'])
    staffing = load_data_file(project_root / config['data']['staffing_file'])
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Overview", "Bottlenecks", "Capacity", "Staffing"]
    )
    
    if page == "Overview":
        show_overview(site_daily, step_daily, config)
    elif page == "Bottlenecks":
        show_bottlenecks(bottlenecks, step_daily)
    elif page == "Capacity":
        show_capacity(step_daily)
    elif page == "Staffing":
        show_staffing(staffing)


def show_overview(site_daily: pd.DataFrame, step_daily: pd.DataFrame, config):
    """Show overview page with key KPIs."""
    st.header("Overview")
    
    if site_daily is None or step_daily is None:
        st.error("Data not available")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_util = site_daily['utilization'].mean()
        st.metric("Average Utilization", f"{avg_util:.1%}")
    
    with col2:
        total_processed = site_daily['processed_units'].sum()
        st.metric("Total Processed", f"{total_processed:,.0f}")
    
    with col3:
        total_loss = site_daily['throughput_loss_units'].sum()
        st.metric("Total Throughput Loss", f"{total_loss:,.0f}")
    
    with col4:
        avg_service = site_daily['service_level_hourly'].mean()
        st.metric("Average Service Level", f"{avg_service:.1%}")
    
    st.markdown("---")
    
    # Site daily chart
    st.subheader("Site Daily Metrics")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=site_daily['date'],
        y=site_daily['processed_units'],
        mode='lines+markers',
        name='Processed Units',
        line=dict(color='#1f77b4')
    ))
    fig.add_trace(go.Scatter(
        x=site_daily['date'],
        y=site_daily['demand_units'],
        mode='lines+markers',
        name='Demand Units',
        line=dict(color='#ff7f0e', dash='dash')
    ))
    
    fig.update_layout(
        title="Daily Throughput: Processed vs Demand",
        xaxis_title="Date",
        yaxis_title="Units",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Utilization by step
    st.subheader("Average Utilization by Step")
    util_by_step = step_daily.groupby('step')['utilization'].mean().reset_index()
    util_by_step = util_by_step.sort_values('utilization', ascending=False)
    
    fig = px.bar(
        util_by_step,
        x='step',
        y='utilization',
        title="Average Utilization by Step",
        labels={'utilization': 'Utilization', 'step': 'Step'},
        color='utilization',
        color_continuous_scale='RdYlGn_r'
    )
    fig.update_layout(height=400, yaxis_tickformat='.1%')
    st.plotly_chart(fig, use_container_width=True)


def show_bottlenecks(bottlenecks: pd.DataFrame, step_daily: pd.DataFrame):
    """Show bottleneck analysis page."""
    st.header("Bottleneck Analysis")
    
    if bottlenecks is None:
        st.error("Bottleneck data not available")
        return
    
    # Filter bottlenecks
    bottleneck_hours = bottlenecks[bottlenecks['is_bottleneck'] == True]
    
    st.metric("Total Bottleneck Hours", len(bottleneck_hours))
    
    st.markdown("---")
    
    # Worst hours table
    st.subheader("Top 10 Worst Hours (by Throughput Loss)")
    worst = bottlenecks.nlargest(10, 'throughput_loss_units')[
        ['timestamp', 'step', 'utilization', 'throughput_loss_units', 'backlog_units']
    ].copy()
    worst['utilization'] = worst['utilization'].apply(lambda x: f"{x:.1%}")
    worst['throughput_loss_units'] = worst['throughput_loss_units'].apply(lambda x: f"{x:,.0f}")
    worst['backlog_units'] = worst['backlog_units'].apply(lambda x: f"{x:,.0f}")
    worst.columns = ['Timestamp', 'Step', 'Utilization', 'Throughput Loss (units)', 'Backlog (units)']
    st.dataframe(worst, use_container_width=True)
    
    st.markdown("---")
    
    # Bottleneck distribution by step
    st.subheader("Bottleneck Distribution by Step")
    if len(bottleneck_hours) > 0:
        bottleneck_dist = bottleneck_hours['step'].value_counts().reset_index()
        bottleneck_dist.columns = ['step', 'count']
        
        fig = px.bar(
            bottleneck_dist,
            x='step',
            y='count',
            title="Bottleneck Hours by Step",
            labels={'count': 'Bottleneck Hours', 'step': 'Step'},
            color='count',
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No bottlenecks detected.")


def show_capacity(step_daily: pd.DataFrame):
    """Show capacity analysis page."""
    st.header("Capacity Analysis")
    
    if step_daily is None:
        st.error("Data not available")
        return
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        date_range = st.date_input(
            "Date Range",
            value=(step_daily['date'].min(), step_daily['date'].max()),
            min_value=step_daily['date'].min(),
            max_value=step_daily['date'].max()
        )
    
    with col2:
        steps = st.multiselect(
            "Steps",
            options=step_daily['step'].unique().tolist(),
            default=step_daily['step'].unique().tolist()
        )
    
    # Filter data
    if isinstance(date_range, tuple) and len(date_range) == 2:
        date_start = pd.to_datetime(date_range[0])
        date_end = pd.to_datetime(date_range[1])
    else:
        date_start = pd.to_datetime(date_range)
        date_end = pd.to_datetime(date_range)
    
    filtered = step_daily[
        (step_daily['step'].isin(steps)) &
        (step_daily['date'] >= date_start) &
        (step_daily['date'] <= date_end)
    ]
    
    if len(filtered) == 0:
        st.warning("No data for selected filters")
        return
    
    st.markdown("---")
    
    # Utilization trends
    st.subheader("Utilization Trends by Step")
    fig = px.line(
        filtered,
        x='date',
        y='utilization',
        color='step',
        title="Daily Utilization by Step",
        labels={'utilization': 'Utilization', 'date': 'Date', 'step': 'Step'}
    )
    fig.update_layout(height=400, yaxis_tickformat='.1%')
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Cycle time trends
    st.subheader("Cycle Time Trends by Step")
    fig = px.line(
        filtered,
        x='date',
        y='cycle_time_min',
        color='step',
        title="Daily Average Cycle Time by Step",
        labels={'cycle_time_min': 'Cycle Time (minutes)', 'date': 'Date', 'step': 'Step'}
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def show_staffing(staffing: pd.DataFrame):
    """Show staffing recommendations page."""
    st.header("Staffing Recommendations")
    
    if staffing is None:
        st.error("Staffing data not available")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_gap = staffing['headcount_gap'].sum()
        st.metric("Total Headcount Gap (hours)", f"{total_gap:,.0f}")
    
    with col2:
        positive_gap = staffing[staffing['headcount_gap'] > 0]['headcount_gap'].sum()
        st.metric("Positive Gap (hours)", f"{positive_gap:,.0f}")
    
    with col3:
        total_cost = staffing['labor_cost_impact'].sum()
        st.metric("Estimated Cost Impact", f"${total_cost:,.2f}")
    
    st.markdown("---")
    
    # Top gaps
    st.subheader("Top 20 Hours with Largest Headcount Gaps")
    top_gaps = staffing.nlargest(20, 'headcount_gap')[
        ['timestamp', 'step', 'headcount_used', 'recommended_headcount', 
         'headcount_gap', 'labor_cost_impact', 'utilization']
    ].copy()
    top_gaps['utilization'] = top_gaps['utilization'].apply(lambda x: f"{x:.1%}")
    top_gaps['labor_cost_impact'] = top_gaps['labor_cost_impact'].apply(lambda x: f"${x:.2f}")
    top_gaps.columns = ['Timestamp', 'Step', 'Current', 'Recommended', 'Gap', 'Cost Impact', 'Utilization']
    st.dataframe(top_gaps, use_container_width=True)
    
    st.markdown("---")
    
    # Gap by step
    st.subheader("Headcount Gap by Step")
    gap_by_step = staffing.groupby('step')['headcount_gap'].sum().reset_index()
    gap_by_step = gap_by_step.sort_values('headcount_gap', ascending=False)
    
    fig = px.bar(
        gap_by_step,
        x='step',
        y='headcount_gap',
        title="Total Headcount Gap by Step",
        labels={'headcount_gap': 'Headcount Gap (hours)', 'step': 'Step'},
        color='headcount_gap',
        color_continuous_scale='Reds'
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Recommended vs actual
    st.subheader("Recommended vs Actual Headcount (Daily Average)")
    daily_avg = staffing.groupby(['step', staffing['timestamp'].dt.date]).agg({
        'headcount_used': 'mean',
        'recommended_headcount': 'mean'
    }).reset_index()
    daily_avg['timestamp'] = pd.to_datetime(daily_avg['timestamp'])
    
    fig = go.Figure()
    for step in daily_avg['step'].unique():
        step_data = daily_avg[daily_avg['step'] == step]
        fig.add_trace(go.Scatter(
            x=step_data['timestamp'],
            y=step_data['headcount_used'],
            mode='lines+markers',
            name=f'{step} - Actual',
            line=dict(dash='solid')
        ))
        fig.add_trace(go.Scatter(
            x=step_data['timestamp'],
            y=step_data['recommended_headcount'],
            mode='lines+markers',
            name=f'{step} - Recommended',
            line=dict(dash='dash')
        ))
    
    fig.update_layout(
        title="Daily Average Headcount: Recommended vs Actual",
        xaxis_title="Date",
        yaxis_title="Headcount",
        hovermode='x unified',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()

