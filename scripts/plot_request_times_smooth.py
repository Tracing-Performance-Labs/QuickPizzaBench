#!/usr/bin/env python3
"""
Smoothed time series plot of HTTP request times with P95/P99 reference lines.
Provides multiple smoothing options to reduce noise and show clearer trends.
"""

import argparse
import gzip
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import re
from scipy.signal import savgol_filter

def plot_request_times_smooth(file_path, smoothing_method='rolling', window_size=50, resample_freq='1S'):
    """Plot smoothed time series of HTTP request duration with percentile lines."""
    
    # Extract config name from filename
    pattern = re.compile(r'(\d+)-quickpizza-(.+)-20vus-60s-t3\.medium\.gz')
    match = pattern.match(Path(file_path).name)
    
    if match:
        date, config = match.groups()
    else:
        config = Path(file_path).stem
    
    print(f"Loading {config} from {file_path}...")
    print(f"Using {smoothing_method} smoothing...")
    
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
    
    # Calculate percentiles on raw data
    p95 = http_duration['metric_value'].quantile(0.95)
    p99 = http_duration['metric_value'].quantile(0.99)
    avg = http_duration['metric_value'].mean()
    max_val = http_duration['metric_value'].max()
    
    # Apply smoothing based on method
    if smoothing_method == 'rolling':
        # Rolling window average
        http_duration['smoothed'] = http_duration['metric_value'].rolling(window=window_size, center=True).mean()
        smooth_label = f'Rolling Average ({window_size} points)'
        
    elif smoothing_method == 'resample':
        # Resample to time buckets (e.g., per-second averages)
        http_duration.set_index('timestamp', inplace=True)
        resampled = http_duration.resample(resample_freq)['metric_value'].agg(['mean', 'std', 'count']).reset_index()
        resampled['relative_time'] = (resampled['timestamp'] - start_time).dt.total_seconds()
        
        # Filter out buckets with too few samples
        resampled = resampled[resampled['count'] >= 3]
        smooth_label = f'Resampled ({resample_freq} buckets)'
        
    elif smoothing_method == 'savgol':
        # Savitzky-Golay filter for trend smoothing
        if len(http_duration) > window_size:
            http_duration['smoothed'] = savgol_filter(http_duration['metric_value'], 
                                                    window_length=window_size if window_size % 2 == 1 else window_size + 1, 
                                                    polyorder=3)
        else:
            # Fall back to rolling average if not enough data
            http_duration['smoothed'] = http_duration['metric_value'].rolling(window=min(10, len(http_duration)//2), center=True).mean()
        smooth_label = f'Savitzky-Golay Filter ({window_size} window)'
        
    elif smoothing_method == 'both':
        # Show both raw (faded) and smoothed data
        http_duration['smoothed'] = http_duration['metric_value'].rolling(window=window_size, center=True).mean()
        smooth_label = f'Rolling Average ({window_size} points)'
    
    # Create plot
    plt.figure(figsize=(14, 8))
    
    if smoothing_method == 'both':
        # Plot raw data as background (very faded)
        plt.plot(http_duration['relative_time'], 
                 http_duration['metric_value'], 
                 color='lightblue', 
                 alpha=0.3,
                 linewidth=0.5,
                 label='Raw Data')
        
        # Plot smoothed data prominently
        plt.plot(http_duration['relative_time'], 
                 http_duration['smoothed'], 
                 color='darkblue', 
                 linewidth=2,
                 label=smooth_label)
                 
    elif smoothing_method == 'resample':
        # Plot resampled data with error bars
        plt.errorbar(resampled['relative_time'], 
                    resampled['mean'],
                    yerr=resampled['std'],
                    color='darkblue', 
                    linewidth=2,
                    capsize=3,
                    alpha=0.8,
                    label=smooth_label)
                    
        # Also plot just the mean line for clarity
        plt.plot(resampled['relative_time'], 
                resampled['mean'], 
                color='navy', 
                linewidth=1.5,
                alpha=0.6)
    else:
        # Plot smoothed data only
        plt.plot(http_duration['relative_time'], 
                 http_duration['smoothed'], 
                 color='darkblue', 
                 linewidth=2,
                 label=smooth_label)
    
    # Plot percentile lines
    plt.axhline(y=p95, 
               color='orange', 
               linestyle='--', 
               linewidth=2,
               label=f'P95: {p95:.1f}ms')
    
    plt.axhline(y=p99, 
               color='red', 
               linestyle=':', 
               linewidth=2,
               label=f'P99: {p99:.1f}ms')
               
    plt.axhline(y=avg, 
               color='green', 
               linestyle='-', 
               linewidth=1,
               alpha=0.7,
               label=f'Average: {avg:.1f}ms')
    
    plt.xlabel('Time (seconds)')
    plt.ylabel('HTTP Request Duration (ms)')
    plt.title(f'HTTP Request Duration Time Series (Smoothed) - {config}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    
    # Save with smoothing method in filename
    output_file = f'request_times_{config}_smooth_{smoothing_method}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"📊 Statistics:")
    print(f"  P95: {p95:.1f}ms")
    print(f"  P99: {p99:.1f}ms")
    print(f"  Average: {avg:.1f}ms")
    print(f"  Max: {max_val:.1f}ms")
    print(f"📈 Smoothed plot saved as: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Plot smoothed HTTP request duration time series from K6 benchmark data')
    parser.add_argument('file', help='Path to gzipped CSV file (e.g., quickpizza-custom-grpc-20vus-60s-t3.medium.gz)')
    parser.add_argument('--method', '-m', 
                       choices=['rolling', 'resample', 'savgol', 'both'], 
                       default='rolling',
                       help='Smoothing method: rolling (moving average), resample (time buckets), savgol (Savitzky-Golay filter), both (raw + smoothed)')
    parser.add_argument('--window', '-w', 
                       type=int, 
                       default=50,
                       help='Window size for rolling average or Savitzky-Golay filter (default: 50)')
    parser.add_argument('--resample-freq', '-r', 
                       default='1S',
                       help='Resampling frequency for resample method (default: 1S = 1 second buckets)')
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"❌ File not found: {args.file}")
        return
    
    try:
        plot_request_times_smooth(args.file, args.method, args.window, args.resample_freq)
    except ImportError as e:
        print(f"❌ Missing libraries: {e}")
        print("💡 Install with: pip install pandas matplotlib scipy")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()