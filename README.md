# Fulfillment Center Capacity Planning & Bottleneck Analysis

A comprehensive analytics pipeline for simulating and analyzing fulfillment center operations, identifying bottlenecks, and generating staffing recommendations to meet service targets.

## Business Context

Fulfillment centers face constant challenges in balancing capacity, demand, and service levels. This project provides a decision-oriented analytics framework that:

- **Simulates realistic FC operations** with hourly granularity across multiple processing steps (receive, pick, pack, ship)
- **Identifies capacity bottlenecks** by analyzing utilization, backlog, and throughput loss
- **Recommends staffing levels** to meet service targets while optimizing labor costs
- **Provides actionable insights** through KPIs and visualizations for operations leaders

## Data Disclaimer

⚠️ **IMPORTANT**: This project uses **synthetic/simulated data**. There is no public FC scan dataset available, so all operational data is generated using realistic models that incorporate:

- Day-of-week and hour-of-day seasonality patterns
- Demand variability and promotional spikes
- Capacity constraints with equipment downtime
- Backlog propagation across processing steps
- Cycle time impacts from congestion

The data generation is **deterministic** (controlled by `random_state` in config) for reproducibility, but represents a simulated operational environment.

## Setup

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Installation

1. Clone or download this repository
2. Navigate to the project directory:
   ```bash
   cd fc-capacity-bottleneck
   ```

3. Create a virtual environment (recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Run Complete Pipeline

To generate data, run all analytics, and produce reports:

```bash
python run.py all
```

This will execute all steps in order:
1. Generate synthetic FC operations data
2. Preprocess and validate data
3. Compute capacity metrics
4. Detect bottlenecks
5. Generate staffing recommendations
6. Create KPI reports

### Individual Steps

You can also run individual steps:

```bash
python run.py generate      # Generate synthetic data
python run.py preprocess    # Preprocess raw data
python run.py analyze       # Compute capacity metrics
python run.py bottlenecks   # Detect bottlenecks
python run.py recommend     # Generate staffing recommendations
python run.py report        # Generate KPI reports
```

### Launch Dashboard

After running the pipeline, launch the Streamlit dashboard:

```bash
python run.py app
```

Or directly:

```bash
streamlit run app/streamlit_app.py
```

The dashboard provides interactive visualizations across four pages:
- **Overview**: Key KPIs and site-level daily trends
- **Bottlenecks**: Worst hours and bottleneck distribution by step
- **Capacity**: Utilization and cycle time trends with filters
- **Staffing**: Recommended vs actual headcount, gaps, and cost impact

## KPI Definitions

### Throughput Metrics
- **Processed Units**: Total units successfully processed across all steps
- **Throughput Loss**: Units that could not be processed due to capacity constraints
- **Service Level**: Fraction of demand processed within the same hour

### Utilization Metrics
- **Utilization**: Ratio of processed units to capacity (0-100%)
- **Average Utilization by Step**: Mean utilization across time period for each processing step

### Cycle Time Metrics
- **Cycle Time**: Time to complete processing at each step (minutes)
- **Average Cycle Time**: Mean cycle time by step
- **P90 Cycle Time**: 90th percentile cycle time (captures worst-case performance)

### Bottleneck Metrics
- **Bottleneck Hours**: Hours where utilization ≥ threshold AND (backlog increasing OR throughput loss > 0)
- **Bottleneck Share**: Percentage of bottleneck occurrences by step

### Staffing Metrics
- **Headcount Gap**: Difference between recommended and actual headcount (hours)
- **Cost Impact**: Estimated additional labor cost to meet service targets

## Decision Derivation

### Bottleneck Detection
Bottlenecks are identified using a two-condition rule:
1. **Utilization threshold**: Utilization ≥ 95% (configurable)
2. **Capacity constraint**: Either backlog is increasing OR throughput loss > 0

This ensures we capture both sustained high utilization and actual service degradation.

### Staffing Recommendations
For each hour and step:
1. **Required Units** = Demand + Incoming Backlog
2. **Required Capacity** = Required Units / Service Target (default 95%)
3. **Required Labor Hours** = Required Capacity / Units Per Hour (UPH)
4. **Recommended Headcount** = Ceiling(Required Labor Hours)

The gap between recommended and actual headcount indicates staffing needs, and cost impact is calculated using hourly wage rates.

## Project Structure

```
fc-capacity-bottleneck/
├── app/
│   └── streamlit_app.py          # Streamlit dashboard
├── config/
│   └── config.yaml                # Configuration parameters
├── data/
│   ├── raw/                       # Generated raw data
│   └── processed/                 # Processed metrics
├── reports/                       # Generated reports (MD, JSON)
├── src/
│   ├── generate_data.py           # Synthetic data generation
│   ├── preprocess.py              # Data preprocessing
│   ├── capacity.py                # Capacity analytics
│   ├── bottleneck.py              # Bottleneck detection
│   ├── recommendations.py         # Staffing recommendations
│   ├── kpis.py                    # KPI computation
│   └── utils.py                   # Utility functions
├── tests/                         # Unit tests
├── venv/                          # Virtual environment (created during setup)
├── run.py                         # Main pipeline runner
├── requirements.txt               # Python dependencies
└── README.md                    # This file
```

## Configuration

Edit `config/config.yaml` to customize:
- **Data generation**: Number of days, demand patterns, seasonality
- **Capacity parameters**: Base capacity by step, variability, downtime
- **Labor productivity**: Units per hour (UPH) by step
- **Service targets**: Target service level (default 95%)
- **Bottleneck threshold**: Utilization threshold for detection (default 95%)

## Testing

Run tests with pytest:

```bash
pytest tests/
```

Tests verify:
- Deterministic data generation
- Expected file creation
- Data schema validation
- Utilization bounds
- Output file generation

## Resume Bullets

For Amazon Operations / Business Analyst roles:

1. **Built end-to-end analytics pipeline** for fulfillment center capacity planning, simulating 56 days of hourly operations data across 4 processing steps (receive, pick, pack, ship) with realistic seasonality, demand variability, and capacity constraints, enabling data-driven bottleneck identification and staffing optimization.

2. **Developed decision-oriented bottleneck detection algorithm** that identifies capacity constraints using utilization thresholds (≥95%) combined with backlog growth and throughput loss metrics, resulting in actionable insights for operations leaders to prioritize resource allocation and reduce service degradation.

3. **Created interactive Streamlit dashboard** with 4 analytical views (Overview, Bottlenecks, Capacity, Staffing) featuring Plotly visualizations, enabling real-time exploration of utilization trends, cycle time analysis, and staffing recommendations with estimated cost impacts to support operational decision-making.

## License

This project is provided as-is for portfolio and educational purposes.

