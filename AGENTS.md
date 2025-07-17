# Agent Guidelines for QuickPizza Benchmark

## Project Purpose
**IMPORTANT**: This is NOT just a pizza API test. This project benchmarks a **custom OpenTelemetry collector** with a deduplication processor for trace data. The QuickPizza API serves as the trace-generating workload to stress test the OTEL collector performance.

## Benchmark Configurations
- `custom` vs `default` - Custom OTEL collector vs default collector
- `grpc` vs `http-json` - Different transport protocols  
- `gzip` - Compression variants
- `no-collector` - Baseline without any collector

## Testing & Benchmarking Commands
- Run benchmark: `./bench.sh <config>`
- Run K6 directly: `k6 run k6-quickpizza.js`
- Set base URL: `BASE_URL=http://localhost:3333 k6 run k6-quickpizza.js`

## Project Structure
This is a K6 performance testing project for benchmarking OTEL collectors. Main files:
- `k6-quickpizza.js` - K6 test script
- `bench.sh` - Benchmark runner script
- `quickpizza-cf-template.yml` - AWS CloudFormation template
- `.gz` files - Compressed benchmark results

## Code Style Guidelines
- JavaScript: Use ES6 imports (`import http from "k6/http"`)
- Variables: Use camelCase (`maxCaloriesPerSlice`, `mustBeVegetarian`)
- Constants: Use UPPER_CASE (`BASE_URL`)
- Bash scripts: Use POSIX-compliant syntax with proper error handling
- YAML: Use 2-space indentation for CloudFormation templates

## Environment Variables
- `BASE_URL` - Target server URL (default: http://localhost:3333)
- `CONFIG` - Benchmark configuration name (required for bench.sh)

## API Conventions
- Content-Type: `application/json`
- Authorization: `token abcdef0123456789`
- Endpoint: `POST /api/pizza` with JSON payload containing restrictions object

## Dataset Analysis & Visualization Scripts

### Dataset Format
Compressed K6 benchmark results (`.gz` files) contain CSV data with columns:
- `metric_name` - Type of metric (http_reqs, http_req_duration, etc.)
- `timestamp` - Unix timestamp 
- `metric_value` - Metric value
- Additional metadata columns (method, status, url, etc.)

### Available Visualization Scripts
- `scripts/plot_request_times.py <file.gz>` - Time series plot of HTTP request durations with P95/P99 percentile lines
- `scripts/plot_rps_cdf.py <file.gz>` - CDF (Cumulative Distribution Function) of requests per second

### Key Metrics for Analysis
- `http_reqs` - Count requests to calculate RPS
- `http_req_duration` - Response times for latency analysis
- `http_req_failed` - Failed request rate

## Python Environment Guidelines

### Virtual Environment Setup
- This project uses `venv` for dependency management
- The virtual environment is located in the `venv/` directory
- Dependencies are managed via `requirements.txt` in the project root

### Python Script Execution Workflow
1. **Always check venv status first** - Verify the virtual environment exists and is properly configured
2. **Ask for permission** - Request user approval before activating venv or running scripts
3. **Activate virtual environment** - Use `source venv/bin/activate` (Linux/Mac) before running Python scripts
4. **Verify dependencies** - Ensure all requirements from `requirements.txt` are installed with `pip install -r requirements.txt`
5. **Execute scripts** - Run Python visualization/analysis scripts only after environment is ready

### Required Dependencies
- pandas>=1.5.0 - Data manipulation and analysis
- matplotlib>=3.6.0 - Basic plotting
- seaborn>=0.12.0 - Statistical visualizations  
- numpy>=1.21.0 - Numerical computations
- scipy>=1.16.0 - Advanced smoothing functions (Savitzky-Golay, interpolation)

## Data Visualization Best Practices

### Smoothing Techniques for Noisy Data
- **Raw benchmark data is often spiky and hard to interpret** - both time series and CDF plots benefit from smoothing
- **Time series smoothing options:**
  - `rolling` - Moving averages for general trend smoothing
  - `resample` - Time bucket aggregation with error bars for statistical analysis
  - `savgol` - Savitzky-Golay filter for preserving peaks while smoothing
  - `both` - Show raw data (faded) + smooth overlay for complete picture
- **CDF smoothing options:**
  - `interpolate` - Cubic spline interpolation for smooth curves
  - `gaussian` - Gaussian filter smoothing
  - `binned` - Histogram binning to reduce noise
  - `both` - Raw stepwise + smooth overlay

### Handling Duplicate Values in Interpolation
- **Problem:** CDF data often has duplicate x-values (same RPS count) which breaks cubic spline interpolation
- **Solution:** Use `np.unique()` to get unique x-values with corresponding y-values for interpolation
- **Important:** This preserves statistical accuracy - we're not removing data points, just making x-axis unique for smooth curve fitting

### Visualization Guidelines for OTEL Benchmarking
- **For executive reports:** Use `resample` (time series) and `interpolate` (CDF) methods for clean, statistical views
- **For engineering analysis:** Use `both` method to show raw data context alongside trends
- **Always include percentile reference lines** (P50, P95, P99) for performance analysis
- **Use consistent smoothing parameters** across configs for fair comparison
