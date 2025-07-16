#!/usr/bin/env python3
"""
Simple time series plot of HTTP request times with P95/P99 reference lines.
"""

import argparse
import gzip
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import re

def plot_request_times(file_path):
    """Plot time series of HTTP request duration with percentile lines for a single file."""
    
    # Extract config name from filename
    pattern = re.compile(r'(\d+)-quickpizza-(.+)-20vus-60s-t3\.medium\.gz')
    match = pattern.match(Path(file_path).name)
    
    if match:
        date, config = match.groups()
    else:
        config = Path(file_path).stem
    
    print(f"Loading {config} from {file_path}...")
    
    # Load data
    with gzip.open(file_path, 'rt') as f:
        df = pd.read_csv(f)
    
    # Filter for HTTP request duration only
    http_duration = df[df['metric_name'] == 'http_req_duration'].copy()
    
    if http_duration.empty:
        print("No HTTP request duration data found!")
        return
    
    # Convert timestamp to datetime
    http_duration['timestamp'] = pd.to_datetime(http_duration['timestamp'], unit='s')
    
    # Sort by timestamp
    http_duration = http_duration.sort_values('timestamp')
    
    # Calculate start time for relative timing
    start_time = http_duration['timestamp'].min()
    http_duration['relative_time'] = (http_duration['timestamp'] - start_time).dt.total_seconds()
    
    # Calculate percentiles
    p95 = http_duration['metric_value'].quantile(0.95)
    p99 = http_duration['metric_value'].quantile(0.99)
    
    # Create plot
    plt.figure(figsize=(12, 6))
    
    # Plot time series
    plt.plot(http_duration['relative_time'], 
             http_duration['metric_value'], 
             color='blue', 
             alpha=0.6,
             linewidth=0.8,
             label='Request Duration')
    
    # Plot P95 line
    plt.axhline(y=p95, 
               color='orange', 
               linestyle='--', 
               linewidth=2,
               label=f'P95: {p95:.1f}ms')
    
    # Plot P99 line  
    plt.axhline(y=p99, 
               color='red', 
               linestyle=':', 
               linewidth=2,
               label=f'P99: {p99:.1f}ms')
    
    plt.xlabel('Time (seconds)')
    plt.ylabel('HTTP Request Duration (ms)')
    plt.title(f'HTTP Request Duration Time Series - {config}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    
    # Save with config name
    output_file = f'request_times_{config}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"📊 Statistics:")
    print(f"  P95: {p95:.1f}ms")
    print(f"  P99: {p99:.1f}ms")
    print(f"  Average: {http_duration['metric_value'].mean():.1f}ms")
    print(f"  Max: {http_duration['metric_value'].max():.1f}ms")
    print(f"📈 Plot saved as: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Plot HTTP request duration time series from K6 benchmark data')
    parser.add_argument('file', help='Path to gzipped CSV file (e.g., quickpizza-custom-grpc-20vus-60s-t3.medium.gz)')
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"❌ File not found: {args.file}")
        return
    
    try:
        plot_request_times(args.file)
    except ImportError as e:
        print(f"❌ Missing libraries: {e}")
        print("💡 Install with: pip install pandas matplotlib")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
