#!/usr/bin/env python3
"""
Storage cost comparison bar chart for OTEL collector configurations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
from pathlib import Path

def parse_size_to_mb(size_str):
    """Convert size string (e.g., '120.1 MiB', '7.0 MiB') to MB float."""
    if 'MiB' in size_str:
        return float(size_str.replace(' MiB', ''))
    elif 'GiB' in size_str:
        return float(size_str.replace(' GiB', '')) * 1024
    elif 'KiB' in size_str:
        return float(size_str.replace(' KiB', '')) / 1024
    else:
        # Assume MB if no unit
        return float(size_str)

def clean_config_name(config_name):
    """Clean up configuration names for better display."""
    # Remove common prefixes and suffixes
    name = config_name.replace('quickpizza-', '').replace('-bucket', '')
    
    # Map to cleaner names
    name_mapping = {
        'http-json': 'Custom HTTP-JSON',
        'default-collector': 'Default Collector',
        'custom-http-json-gzip': 'Custom HTTP-JSON+gzip',
        'custom-grcp-gzip': 'Custom gRPC+gzip',  # Note: typo in original data
        'custom-grpc': 'Custom gRPC'
    }
    
    return name_mapping.get(name, name.title())

def plot_storage_comparison(csv_file, show_savings=True, show_cost_estimate=False, cost_per_gb_month=0.023):
    """Create side-by-side storage comparison bar chart."""
    
    print(f"Loading storage data from {csv_file}...")
    
    # Read the CSV data
    df = pd.read_csv(csv_file)
    
    # Parse sizes to MB
    df['size_mb'] = df['total size'].apply(parse_size_to_mb)
    
    # Clean configuration names
    df['clean_config'] = df['configuration'].apply(clean_config_name)
    
    # Calculate savings percentages relative to default
    default_size = df[df['clean_config'] == 'Default Collector']['size_mb'].iloc[0]
    default_objects = df[df['clean_config'] == 'Default Collector']['total objects'].iloc[0]
    df['savings_percent'] = ((default_size - df['size_mb']) / default_size) * 100
    df['object_change_percent'] = ((df['total objects'] - default_objects) / default_objects) * 100
    
    # Sort by size for better visualization
    df = df.sort_values('size_mb', ascending=False)
    
    # Create the plot with two subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Color scheme: red for default, green gradient for savings
    size_colors = []
    object_colors = []
    for idx, row in df.iterrows():
        if 'Default' in row['clean_config']:
            size_colors.append('#e74c3c')  # Red for baseline
            object_colors.append('#e74c3c')  # Red for baseline
        elif row['savings_percent'] > 90:
            size_colors.append('#27ae60')  # Dark green for massive savings
        elif row['savings_percent'] > 50:
            size_colors.append('#2ecc71')  # Green for good savings
        elif row['savings_percent'] > 0:
            size_colors.append('#f39c12')  # Orange for moderate savings
        else:
            size_colors.append('#e67e22')  # Dark orange for worse than default
            
        # Object count colors (different logic - more objects could be good or bad)
        if 'Default' not in row['clean_config']:
            if row['object_change_percent'] > 0:
                object_colors.append('#3498db')  # Blue for more objects
            elif row['object_change_percent'] < 0:
                object_colors.append('#9b59b6')  # Purple for fewer objects
            else:
                object_colors.append('#95a5a6')  # Gray for same
    
    # === LEFT PLOT: Storage Size ===
    bars1 = ax1.bar(df['clean_config'], df['size_mb'], color=size_colors, alpha=0.8, edgecolor='black', linewidth=1)
    
    # Add value labels on bars
    for bar, size, savings in zip(bars1, df['size_mb'], df['savings_percent']):
        height = bar.get_height()
        
        # Size label
        ax1.text(bar.get_x() + bar.get_width()/2., height + max(df['size_mb']) * 0.02,
                f'{size:.1f} MiB',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        # Savings percentage (if showing savings and not default)
        if show_savings and savings > 0:
            ax1.text(bar.get_x() + bar.get_width()/2., height/2,
                    f'-{savings:.0f}%',
                    ha='center', va='center', fontweight='bold', 
                    fontsize=11, color='white')
    
    # Formatting for storage size chart
    ax1.set_ylabel('Storage Size (MiB)', fontsize=12, fontweight='bold')
    ax1.set_title('Storage Size Comparison', fontsize=14, fontweight='bold')
    ax1.grid(True, axis='y', alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # === RIGHT PLOT: Object Count ===
    bars2 = ax2.bar(df['clean_config'], df['total objects'], color=object_colors, alpha=0.8, edgecolor='black', linewidth=1)
    
    # Add value labels on bars
    for bar, objects, change in zip(bars2, df['total objects'], df['object_change_percent']):
        height = bar.get_height()
        
        # Object count label
        ax2.text(bar.get_x() + bar.get_width()/2., height + max(df['total objects']) * 0.02,
                f'{int(objects)}',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        # Change percentage (if showing savings and not default)
        if show_savings and change != 0:
            change_str = f'+{change:.0f}%' if change > 0 else f'{change:.0f}%'
            ax2.text(bar.get_x() + bar.get_width()/2., height/2,
                    change_str,
                    ha='center', va='center', fontweight='bold', 
                    fontsize=11, color='white')
    
    # Formatting for object count chart
    ax2.set_ylabel('Number of Objects', fontsize=12, fontweight='bold')
    ax2.set_title('Object Count Comparison', fontsize=14, fontweight='bold')
    ax2.grid(True, axis='y', alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    # Add cost estimate if requested
    if show_cost_estimate:
        monthly_costs = (df['size_mb'] / 1024) * cost_per_gb_month  # Convert MB to GB and multiply by cost
        
        # Add cost annotations to size chart
        for i, (bar, cost) in enumerate(zip(bars1, monthly_costs)):
            ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(df['size_mb']) * 0.05,
                    f'${cost:.3f}/mo',
                    ha='center', va='bottom', fontsize=9, style='italic', color='gray')
    
    # Add legends
    size_legend_elements = [
        plt.Rectangle((0,0),1,1, facecolor='#e74c3c', label='Baseline (Default)'),
        plt.Rectangle((0,0),1,1, facecolor='#f39c12', label='Moderate Savings'),
        plt.Rectangle((0,0),1,1, facecolor='#2ecc71', label='Good Savings (>50%)'),
        plt.Rectangle((0,0),1,1, facecolor='#27ae60', label='Massive Savings (>90%)')
    ]
    ax1.legend(handles=size_legend_elements, loc='upper right', fontsize=9)
    
    object_legend_elements = [
        plt.Rectangle((0,0),1,1, facecolor='#e74c3c', label='Baseline (Default)'),
        plt.Rectangle((0,0),1,1, facecolor='#3498db', label='More Objects'),
        plt.Rectangle((0,0),1,1, facecolor='#9b59b6', label='Fewer Objects')
    ]
    ax2.legend(handles=object_legend_elements, loc='upper right', fontsize=9)
    
    plt.tight_layout()
    
    # Save the plot
    output_file = 'storage_comparison_bar_chart.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print summary statistics
    print(f"\n📊 Storage Comparison Summary:")
    print(f"{'Configuration':<25} {'Size (MiB)':<12} {'Size Change':<12} {'Objects':<8} {'Obj Change':<10}")
    print("-" * 75)
    
    for _, row in df.iterrows():
        size_change_str = f"{row['savings_percent']:+.0f}%" if row['savings_percent'] != 0 else "baseline"
        obj_change_str = f"{row['object_change_percent']:+.0f}%" if row['object_change_percent'] != 0 else "baseline"
        print(f"{row['clean_config']:<25} {row['size_mb']:<12.1f} {size_change_str:<12} {row['total objects']:<8} {obj_change_str:<10}")
    
    print(f"\n📈 Chart saved as: {output_file}")
    print(f"💾 Best storage efficiency: {df.loc[df['size_mb'].idxmin(), 'clean_config']} ({df['size_mb'].min():.1f} MiB)")
    print(f"📦 Object count range: {df['total objects'].min()}-{df['total objects'].max()} objects")
    print(f"💰 Potential savings: Up to {df['savings_percent'].max():.0f}% reduction in storage costs")

def main():
    parser = argparse.ArgumentParser(description='Create storage comparison bar chart for OTEL collector configurations')
    parser.add_argument('file', help='Path to CSV file with storage results')
    parser.add_argument('--no-savings', action='store_true', help='Hide savings percentages on bars')
    parser.add_argument('--cost-estimate', action='store_true', help='Show estimated monthly costs')
    parser.add_argument('--cost-per-gb', type=float, default=0.023, help='Cost per GB per month (default: $0.023 for AWS S3)')
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"❌ File not found: {args.file}")
        return
    
    try:
        plot_storage_comparison(args.file, 
                              show_savings=not args.no_savings,
                              show_cost_estimate=args.cost_estimate,
                              cost_per_gb_month=args.cost_per_gb)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()