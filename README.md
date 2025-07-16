# QuickPizza OTEL Collector Benchmark

A performance benchmarking suite for testing custom OpenTelemetry (OTEL) collectors with deduplication processors using the QuickPizza API as a trace-generating workload.

## Overview

This project benchmarks a **custom OpenTelemetry collector** that includes a deduplication processor for trace data. The QuickPizza API serves as a realistic trace-generating workload to stress test the OTEL collector's performance under various configurations.

## Benchmark Configurations

The test suite evaluates different collector configurations:

- **Custom vs Default**: Custom OTEL collector with deduplication vs standard collector
- **Transport Protocols**: `grpc` vs `http-json` 
- **Compression**: `gzip` variants for reduced payload size
- **Baseline**: `no-collector` configuration for performance comparison

## Quick Start

### Prerequisites

- [K6](https://k6.io/) load testing tool
- Access to QuickPizza API endpoint (default: `http://localhost:3333`)

### Running Benchmarks

```bash
# Run a specific benchmark configuration
./scripts/bench.sh custom-http-json-gzip

# Run K6 directly with custom base URL
BASE_URL=http://your-server:3333 k6 run scripts/k6-quickpizza.js

# Run basic test
k6 run scripts/k6-quickpizza.js
```

## Test Configuration

The K6 script (`scripts/k6-quickpizza.js`) runs with:
- **20 virtual users** for **60 seconds**
- POST requests to `/api/pizza` endpoint
- JSON payload with pizza restrictions
- Authorization token: `abcdef0123456789`
- **Note**: No sleep between requests (stress test mode)

## Infrastructure Deployment

Deploy test infrastructure on AWS using the provided CloudFormation template:

```bash
aws cloudformation create-stack \
  --stack-name quickpizza-benchmark \
  --template-body file://templates/quickpizza-cf-template.yml \
  --parameters ParameterKey=KeyName,ParameterValue=your-key \
               ParameterKey=S3BucketName,ParameterValue=your-unique-bucket
```

**Infrastructure includes:**
- Ubuntu EC2 instance (t3.medium) with Docker
- VPC with public subnet and security groups
- S3 bucket for result storage
- Ports: 22 (SSH), 80 (HTTP), 3333 (QuickPizza API)

## Results

Benchmark results are stored in the `datasets/` directory as compressed CSV files with naming pattern:
```
datasets/DDMMYY-quickpizza-<config>-20vus-60s-t3.medium.gz
```

Example configurations tested:
- `custom-http-json` vs `default-http-json`
- `custom-grpc` vs `custom-grpc-gzip`  
- `default-no-collector` (baseline)

## Data Visualization

Visualize request timing data using the provided plotting script:

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Plot time series for a specific benchmark
python3 scripts/plot_request_times.py datasets/160725-quickpizza-custom-grpc-20vus-60s-t3.medium.gz
```

**Output**: Time series plot with P95 and P99 reference lines saved as PNG.

## Environment Variables

- `BASE_URL`: Target server URL (default: `http://localhost:3333`)
- `CONFIG`: Benchmark configuration name (required for `bench.sh`)

## API Details

The test targets the QuickPizza API endpoint:
- **Endpoint**: `POST /api/pizza`
- **Content-Type**: `application/json`
- **Authorization**: `token abcdef0123456789`

Sample payload:
```json
{
  "maxCaloriesPerSlice": 500,
  "mustBeVegetarian": false,
  "excludedIngredients": ["pepperoni"],
  "excludedTools": ["knife"],
  "maxNumberOfToppings": 6,
  "minNumberOfToppings": 2
}
```

## Project Structure

```
QuickPizzaBench/
├── datasets/              # Benchmark result files (.gz)
├── scripts/               # Benchmark and analysis scripts
│   ├── bench.sh          # Benchmark runner
│   ├── k6-quickpizza.js  # K6 load test script
│   ├── plot_request_times.py  # Visualization script
│   └── requirements.txt  # Python dependencies
├── templates/             # Infrastructure templates
│   └── quickpizza-cf-template.yml
├── AGENTS.md             # Agent guidelines
└── README.md
```

## Contributing

When adding new benchmark configurations, follow the naming convention:
`<collector-type>-<protocol>-<compression>-<additional-options>`
