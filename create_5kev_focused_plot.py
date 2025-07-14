#!/usr/bin/env python3
"""
Create a focused plot for 5keV integrated map with specific requirements:
- Axis limits 200-900 on both x and y
- 1:1 aspect ratio
- Title with beam energy and peak rate
- Annotation about azimuth walk
- Save as PNG and SVG (scalar)
"""

import sys
import os
sys.path.append('src')
from integrated_map_analysis import IntegratedMapAnalyzer
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

def create_5kev_focused_plot():
    """Create focused 5keV integrated plot with specific requirements."""
    
    print("🎯 Creating Focused 5keV Integrated Plot")
    print("=" * 45)
    
    # Initialize analyzer
    analyzer = IntegratedMapAnalyzer("data")
    
    # Find 5keV map files
    print("🔍 Finding 5keV map files...")
    map_files_5kev = analyzer.find_map_files(beam_energy=5000.0)
    
    if not map_files_5kev:
        print("❌ No 5keV map files found")
        return
    
    print(f"✅ Found {len(map_files_5kev)} 5keV map files")
    
    # Analyze contributions
    print("🔬 Analyzing 5keV map contributions...")
    contributions = analyzer.analyze_map_contributions(map_files_5kev)
    
    if not contributions:
        print("❌ No valid 5keV contributions found")
        return
    
    print(f"✅ Found {len(contributions)} valid contributions")
    
    # Create integrated map
    print("🗺️  Creating integrated 5keV map...")
    integrated_map, metadata = analyzer.create_integrated_map(contributions)
    
    print(f"✅ Integration complete!")
    print(f"   Peak integrated rate: {metadata['peak_integrated_rate']:.1f} counts/s")
    print(f"   Total files: {metadata['total_files']}")
    
    # Create the focused plot
    print("📊 Creating focused plot...")
    create_focused_plot(integrated_map, metadata, contributions)
    
    print("✅ Focused 5keV plot creation complete!")


def create_focused_plot(integrated_map, metadata, contributions):
    """Create the focused plot with specific requirements."""
    
    # Create figure with 1:1 aspect ratio
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    
    # Calculate log scale limits for the cropped region
    # Extract the region of interest (200-900 on both axes)
    x_min, x_max = 200, 900
    y_min, y_max = 200, 900
    
    # Crop the integrated map to the region of interest
    cropped_map = integrated_map[y_min:y_max, x_min:x_max]
    
    # Calculate appropriate log scale limits for the cropped region
    nonzero_data = cropped_map[cropped_map > 0]
    if len(nonzero_data) > 0:
        vmin_log = max(0.01, np.min(nonzero_data))
        vmax_log = np.max(nonzero_data)
    else:
        vmin_log, vmax_log = 0.01, 1.0
    
    print(f"   Cropped region: {cropped_map.shape}")
    print(f"   Log scale range: {vmin_log:.3f} - {vmax_log:.1f} counts/s")
    print(f"   Non-zero pixels in crop: {len(nonzero_data):,}")
    
    # Create the plot with log scale
    im = ax.imshow(cropped_map, cmap='hot', aspect='equal', origin='lower',
                   extent=[x_min, x_max, y_min, y_max],
                   norm=LogNorm(vmin=vmin_log, vmax=vmax_log))
    
    # Add contour lines for better visibility
    if len(nonzero_data) > 0:
        # Create contour levels at different percentiles
        percentiles = [50, 75, 90, 95, 99]
        contour_levels = [np.percentile(nonzero_data, p) for p in percentiles]
        
        # Create coordinate arrays for contour (for the cropped region)
        y_coords, x_coords = np.mgrid[y_min:y_max, x_min:x_max]
        
        # Add contour lines
        contours = ax.contour(x_coords, y_coords, cropped_map, 
                            levels=contour_levels, colors='white', 
                            linewidths=1.0, alpha=0.8)
        
        # Add contour labels for the highest levels only
        high_levels = contour_levels[-2:]  # Top 2 levels
        if len(high_levels) > 0:
            ax.clabel(contours, levels=high_levels, inline=True, fontsize=8, fmt='%.1f')
    
    # Set axis limits and aspect ratio
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')
    
    # Labels
    ax.set_xlabel('X Position (pixels)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y Position (pixels)', fontsize=12, fontweight='bold')
    
    # Title with beam energy and peak rate
    beam_energy = 5000  # eV
    peak_rate = metadata['peak_integrated_rate']
    title = f'{beam_energy/1000:.0f} keV Beam Energy\nPeak Rate: {peak_rate:.1f} counts/s'
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Count Rate (counts/s, log scale)', fontsize=11, fontweight='bold')
    
    # Add annotation about azimuth sweep
    # Place annotation in upper right corner of the plot area
    annotation_text = 'Azimuth sweep\nduring data collection'
    ax.annotate(annotation_text,
                xy=(0.95, 0.95), xycoords='axes fraction',
                fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8),
                verticalalignment='top', horizontalalignment='right')
    
    # Add grid for better readability
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Ensure tight layout
    plt.tight_layout()
    
    # Create output directory
    os.makedirs("results", exist_ok=True)
    
    # Save as PNG (raster)
    png_path = "results/5keV_focused_integrated_map.png"
    plt.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"   📊 PNG saved: {png_path}")
    
    # Save as SVG (vector/scalar)
    svg_path = "results/5keV_focused_integrated_map.svg"
    plt.savefig(svg_path, format='svg', bbox_inches='tight', facecolor='white')
    print(f"   📊 SVG saved: {svg_path}")
    
    # Also save as PDF (another vector format)
    pdf_path = "results/5keV_focused_integrated_map.pdf"
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', facecolor='white')
    print(f"   📊 PDF saved: {pdf_path}")
    
    # Show plot information
    print(f"\n📋 Plot Details:")
    print(f"   Beam Energy: {beam_energy} eV")
    print(f"   Peak Rate: {peak_rate:.1f} counts/s")
    print(f"   Axis Limits: X({x_min}-{x_max}), Y({y_min}-{y_max}) pixels")
    print(f"   Aspect Ratio: 1:1")
    print(f"   Colormap: 'hot' with log scale")
    print(f"   Contour Levels: {len(contour_levels)} percentile-based")
    print(f"   Files Integrated: {metadata['total_files']}")
    
    # Display the plot
    plt.show()


def main():
    """Main function."""
    try:
        create_5kev_focused_plot()
    except Exception as e:
        print(f"❌ Error creating focused plot: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
