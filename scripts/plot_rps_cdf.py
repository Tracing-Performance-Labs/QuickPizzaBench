#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import gzip

def main():
    if len(sys.argv) != 2:
        print("Usage: python plot_rps_cdf.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    # Read the file (handle both .gz and regular files)
    if filename.endswith('.gz'):
        with gzip.open(filename, 'rt') as f:
            df = pd.read_csv(f)
    else:
        df = pd.read_csv(filename)
    
    # Filter for http_reqs metric only
    http_reqs = df[df['metric_name'] == 'http_reqs'].copy()
    
    # Convert timestamp to datetime
    http_reqs['datetime'] = pd.to_datetime(http_reqs['timestamp'], unit='s')
    
    # Round to seconds and count requests per second
    http_reqs['second'] = http_reqs['datetime'].dt.floor('S')
    rps = http_reqs.groupby('second').size()
    
    # Create CDF
    sorted_rps = np.sort(rps.values)
    cumulative = np.arange(1, len(sorted_rps) + 1) / len(sorted_rps)
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(sorted_rps, cumulative, linewidth=2)
    plt.xlabel('Requests per Second')
    plt.ylabel('Cumulative Probability')
    plt.title(f'CDF of Requests per Second - {filename}')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save and show
    output_name = filename.replace('.gz', '').replace('.csv', '') + '_rps_cdf.png'
    plt.savefig(output_name, dpi=150, bbox_inches='tight')
    print(f"Plot saved as: {output_name}")
    plt.show()

if __name__ == "__main__":
    main()