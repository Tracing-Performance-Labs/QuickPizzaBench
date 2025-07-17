#!/usr/bin/env python3
"""
Smoothed CDF plot of requests per second with multiple smoothing options.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import gzip
import argparse
from pathlib import Path
from scipy.interpolate import interp1d
from scipy.ndimage import gaussian_filter1d

def plot_rps_cdf_smooth(filename, smoothing_method='interpolate', smoothing_factor=0.5, num_points=500):
    """Plot smoothed CDF of requests per second."""
    
    print(f"Loading RPS data from {filename}...")
    print(f"Using {smoothing_method} smoothing...")
    
    # Read the file (handle both .gz and regular files)
    if filename.endswith('.gz'):
        with gzip.open(filename, 'rt') as f:
            df = pd.read_csv(f)
    else:
        df = pd.read_csv(filename)
    
    # Filter for http_reqs metric only
    http_reqs = df[df['metric_name'] == 'http_reqs'].copy()
    
    if http_reqs.empty:
        print("No HTTP requests data found!")
        return
    
    # Convert timestamp to datetime
    http_reqs['datetime'] = pd.to_datetime(http_reqs['timestamp'], unit='s')
    
    # Round to seconds and count requests per second
    http_reqs['second'] = http_reqs['datetime'].dt.floor('s')
    rps = http_reqs.groupby('second').size()
    
    # Create raw CDF data
    sorted_rps = np.sort(rps.values)
    cumulative = np.arange(1, len(sorted_rps) + 1) / len(sorted_rps)
    
    # Remove duplicates for interpolation (keep unique x values with corresponding y values)
    unique_rps, unique_indices = np.unique(sorted_rps, return_index=True)
    unique_cumulative = cumulative[unique_indices]
    
    # Calculate statistics
    p50 = np.percentile(sorted_rps, 50)
    p95 = np.percentile(sorted_rps, 95)
    p99 = np.percentile(sorted_rps, 99)
    mean_rps = np.mean(sorted_rps)
    max_rps = np.max(sorted_rps)
    
    # Apply smoothing based on method
    if smoothing_method == 'interpolate':
        # Cubic spline interpolation for smooth curve
        if len(unique_rps) > 4:  # Need at least 4 points for cubic
            f = interp1d(unique_rps, unique_cumulative, kind='cubic', bounds_error=False, fill_value=(0, 1))
            smooth_x = np.linspace(unique_rps.min(), unique_rps.max(), num_points)
            smooth_y = f(smooth_x)
            # Remove any NaN values
            mask = ~np.isnan(smooth_y)
            smooth_x, smooth_y = smooth_x[mask], smooth_y[mask]
        else:
            smooth_x, smooth_y = unique_rps, unique_cumulative
        smooth_label = f'Interpolated CDF ({num_points} points)'
        
    elif smoothing_method == 'gaussian':
        # Gaussian filter smoothing
        sigma = smoothing_factor * len(sorted_rps) / 100  # Convert factor to sigma
        smooth_y = gaussian_filter1d(cumulative, sigma=sigma)
        smooth_x = sorted_rps
        smooth_label = f'Gaussian Smoothed (σ={sigma:.1f})'
        
    elif smoothing_method == 'binned':
        # Bin the data to reduce noise
        num_bins = max(20, int(len(sorted_rps) * smoothing_factor))
        bin_edges = np.linspace(sorted_rps.min(), sorted_rps.max(), num_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Calculate CDF for each bin
        smooth_y = []
        for edge in bin_centers:
            smooth_y.append(np.mean(sorted_rps <= edge))
        
        smooth_x = bin_centers
        smooth_y = np.array(smooth_y)
        smooth_label = f'Binned CDF ({num_bins} bins)'
        
    elif smoothing_method == 'both':
        # Show both raw and smoothed
        if len(unique_rps) > 4:
            f = interp1d(unique_rps, unique_cumulative, kind='cubic', bounds_error=False, fill_value=(0, 1))
            smooth_x = np.linspace(unique_rps.min(), unique_rps.max(), num_points)
            smooth_y = f(smooth_x)
            mask = ~np.isnan(smooth_y)
            smooth_x, smooth_y = smooth_x[mask], smooth_y[mask]
        else:
            smooth_x, smooth_y = unique_rps, unique_cumulative
        smooth_label = f'Interpolated CDF'
    
    # Create plot
    plt.figure(figsize=(12, 8))
    
    if smoothing_method == 'both':
        # Plot raw data as steps (faded)
        plt.step(sorted_rps, cumulative, where='post', 
                color='lightblue', alpha=0.6, linewidth=1, label='Raw CDF (steps)')
        
        # Plot smoothed curve
        plt.plot(smooth_x, smooth_y, color='darkblue', linewidth=2.5, label=smooth_label)
    else:
        # Plot smoothed data only
        if smoothing_method == 'binned':
            plt.step(smooth_x, smooth_y, where='mid', 
                    color='darkblue', linewidth=2, label=smooth_label)
        else:
            plt.plot(smooth_x, smooth_y, color='darkblue', linewidth=2.5, label=smooth_label)
    
    # Add percentile lines
    plt.axvline(x=p50, color='green', linestyle='-', alpha=0.7, linewidth=1.5, label=f'P50: {p50:.1f} RPS')
    plt.axvline(x=p95, color='orange', linestyle='--', linewidth=2, label=f'P95: {p95:.1f} RPS')
    plt.axvline(x=p99, color='red', linestyle=':', linewidth=2, label=f'P99: {p99:.1f} RPS')
    
    plt.xlabel('Requests per Second')
    plt.ylabel('Cumulative Probability')
    
    # Extract config name from filename for title
    config_name = Path(filename).stem.replace('-20vus-60s-t3.medium', '')
    plt.title(f'Smoothed CDF of Requests per Second - {config_name}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    # Save with smoothing method in filename
    base_name = Path(filename).stem.replace('.gz', '')
    output_name = f'{base_name}_rps_cdf_smooth_{smoothing_method}.png'
    plt.savefig(output_name, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"📊 RPS Statistics:")
    print(f"  P50: {p50:.1f} RPS")
    print(f"  P95: {p95:.1f} RPS") 
    print(f"  P99: {p99:.1f} RPS")
    print(f"  Mean: {mean_rps:.1f} RPS")
    print(f"  Max: {max_rps:.1f} RPS")
    print(f"📈 Smoothed CDF plot saved as: {output_name}")

def main():
    parser = argparse.ArgumentParser(description='Plot smoothed CDF of requests per second from K6 benchmark data')
    parser.add_argument('file', help='Path to gzipped CSV file')
    parser.add_argument('--method', '-m', 
                       choices=['interpolate', 'gaussian', 'binned', 'both'], 
                       default='interpolate',
                       help='Smoothing method: interpolate (cubic spline), gaussian (filter), binned (histogram), both (raw + smooth)')
    parser.add_argument('--factor', '-f', 
                       type=float, 
                       default=0.5,
                       help='Smoothing factor (0.1-2.0, default: 0.5)')
    parser.add_argument('--points', '-p', 
                       type=int, 
                       default=500,
                       help='Number of interpolation points (default: 500)')
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"❌ File not found: {args.file}")
        return
    
    try:
        plot_rps_cdf_smooth(args.file, args.method, args.factor, args.points)
    except ImportError as e:
        print(f"❌ Missing libraries: {e}")
        print("💡 Install with: pip install pandas matplotlib scipy")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()