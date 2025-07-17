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