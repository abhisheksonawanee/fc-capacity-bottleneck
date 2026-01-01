# Project Status & Validation Checklist

## Quick Validation

### Prerequisites Check
- [x] Python 3.10+ installed
- [x] Dependencies installed (`pip install -r requirements.txt`)
- [x] Project structure created

### Pipeline Execution
- [ ] Run `python run.py all` successfully
- [ ] All data files generated in `data/` directories
- [ ] All reports generated in `reports/` directory
- [ ] Streamlit app launches without errors

## Expected Generated Outputs

### Data Files

#### Raw Data
- **File**: `data/raw/fc_hourly_ops.csv`
- **Description**: Synthetic hourly operations data for all steps
- **Columns**: timestamp, step, demand_units, capacity_units, processed_units, backlog_units, utilization, cycle_time_min, uph, labor_hours_used, headcount_used
- **Rows**: 24 hours × num_days × 4 steps (default: 5,376 rows)

#### Processed Data
- **File**: `data/processed/fc_hourly_ops_clean.csv`
- **Description**: Cleaned data with derived features
- **Additional Columns**: date, dow, hour, is_weekend

#### Metrics Files
- **File**: `data/processed/step_hourly_metrics.csv`
- **Description**: Hourly aggregated metrics by step
- **Key Metrics**: utilization, service_level_hourly, throughput_loss_units

- **File**: `data/processed/step_daily_metrics.csv`
- **Description**: Daily aggregated metrics by step
- **Key Metrics**: Daily totals and averages by step

- **File**: `data/processed/site_daily_metrics.csv`
- **Description**: Daily aggregated metrics across all steps
- **Key Metrics**: Site-level daily totals

#### Analysis Files
- **File**: `data/processed/bottlenecks.csv`
- **Description**: Bottleneck flags and analysis
- **Key Columns**: is_bottleneck, bottleneck_step

- **File**: `data/processed/staffing_recommendations.csv`
- **Description**: Staffing recommendations by hour and step
- **Key Columns**: recommended_headcount, headcount_gap, labor_cost_impact

### Reports

#### Bottleneck Summary
- **File**: `reports/bottleneck_summary.md`
- **Contents**: 
  - Total bottleneck hours
  - Bottleneck hours by step
  - Top 10 worst hours table
  - Bottleneck step distribution

#### Staffing Summary
- **File**: `reports/staffing_summary.md`
- **Contents**:
  - Total headcount gap
  - Cost impact
  - Headcount gap by step
  - Top 20 hours with largest gaps
  - Recommendations

#### KPI Reports
- **File**: `reports/kpis.json`
- **Description**: Machine-readable KPI data

- **File**: `reports/kpis.md`
- **Description**: Human-readable KPI report with tables
- **Contents**:
  - Overview metrics
  - Throughput metrics
  - Utilization by step
  - Cycle time metrics
  - Bottleneck analysis
  - Staffing recommendations

## Validation Steps

### 1. Data Generation
```bash
python run.py generate
```
**Check**:
- [ ] `data/raw/fc_hourly_ops.csv` exists
- [ ] File has expected columns
- [ ] Data spans expected date range
- [ ] All 4 steps present (receive, pick, pack, ship)

### 2. Preprocessing
```bash
python run.py preprocess
```
**Check**:
- [ ] `data/processed/fc_hourly_ops_clean.csv` exists
- [ ] Additional feature columns present (date, dow, hour, is_weekend)
- [ ] No missing values in critical columns

### 3. Capacity Analytics
```bash
python run.py analyze
```
**Check**:
- [ ] `data/processed/step_hourly_metrics.csv` exists
- [ ] `data/processed/step_daily_metrics.csv` exists
- [ ] `data/processed/site_daily_metrics.csv` exists
- [ ] Utilization values in [0, 1] range
- [ ] Service level values in [0, 1] range

### 4. Bottleneck Analysis
```bash
python run.py bottlenecks
```
**Check**:
- [ ] `data/processed/bottlenecks.csv` exists
- [ ] `reports/bottleneck_summary.md` exists
- [ ] Bottleneck flags present (is_bottleneck column)
- [ ] Summary report is readable

### 5. Staffing Recommendations
```bash
python run.py recommend
```
**Check**:
- [ ] `data/processed/staffing_recommendations.csv` exists
- [ ] `reports/staffing_summary.md` exists
- [ ] Recommended headcount >= 0
- [ ] Cost impact calculated

### 6. KPI Reports
```bash
python run.py report
```
**Check**:
- [ ] `reports/kpis.json` exists
- [ ] `reports/kpis.md` exists
- [ ] JSON is valid
- [ ] Markdown report is readable

### 7. Dashboard
```bash
python run.py app
```
**Check**:
- [ ] Dashboard loads without errors
- [ ] All 4 pages accessible (Overview, Bottlenecks, Capacity, Staffing)
- [ ] Charts render correctly
- [ ] Filters work as expected
- [ ] No missing data warnings

## Common Issues

### Issue: "Config file not found"
**Solution**: Ensure you're running from project root directory

### Issue: "Raw data file not found" (during preprocessing)
**Solution**: Run `python run.py generate` first

### Issue: "Hourly metrics file not found" (during bottleneck analysis)
**Solution**: Run `python run.py analyze` first

### Issue: Dashboard shows "Required data files are missing"
**Solution**: Run `python run.py all` to generate all required files

### Issue: Import errors
**Solution**: Ensure you're in the project root and dependencies are installed

## Performance Expectations

- **Data Generation**: ~5-10 seconds for 56 days
- **Preprocessing**: ~1-2 seconds
- **Capacity Analytics**: ~2-3 seconds
- **Bottleneck Analysis**: ~1-2 seconds
- **Staffing Recommendations**: ~1-2 seconds
- **KPI Reports**: ~1 second
- **Total Pipeline**: ~15-20 seconds

## File Size Estimates

- Raw data CSV: ~500 KB - 1 MB
- Processed data CSV: ~600 KB - 1.2 MB
- Metrics CSVs: ~200-400 KB each
- Reports (MD): ~5-10 KB each
- KPI JSON: ~2-5 KB

## Next Steps After Validation

1. Review generated reports in `reports/` directory
2. Explore dashboard interactively
3. Adjust configuration in `config/config.yaml` if needed
4. Run tests: `pytest tests/`
5. Customize for your use case

