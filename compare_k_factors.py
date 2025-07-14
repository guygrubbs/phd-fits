#!/usr/bin/env python3
"""
Side-by-side k-factor comparison for 1keV and 5keV beam energies.
"""

import sys
import os
sys.path.append('src')
from esa_analysis import ESAAnalyzer
from data_model import DataManager
import numpy as np
import matplotlib.pyplot as plt


def calculate_manual_k_factor(regions, energy_label):
    """Calculate k-factor manually when automatic estimation fails."""

    print(f"   🔧 Calculating {energy_label} k-factor manually...")

    k_factors = []
    measurements = []

    for region in regions:
        if region.beam_energy and region.esa_voltage:
            k_factor = region.beam_energy / abs(region.esa_voltage)
            k_factors.append(k_factor)

            # Create a simple measurement object
            class SimpleMeasurement:
                def __init__(self, region, k_factor):
                    self.impact_region = region
                    self.k_factor_estimate = k_factor

            measurements.append(SimpleMeasurement(region, k_factor))

            print(f"      {region.filename}: {region.beam_energy:.0f} eV / {abs(region.esa_voltage):.0f} V = {k_factor:.2f} eV/V")

    if k_factors:
        results = {
            'mean_k_factor': np.mean(k_factors),
            'std_k_factor': np.std(k_factors),
            'min_k_factor': np.min(k_factors),
            'max_k_factor': np.max(k_factors),
            'measurements': measurements
        }

        print(f"   ✅ Manual {energy_label} k-factor: {results['mean_k_factor']:.2f} ± {results['std_k_factor']:.3f} eV/V")
        return results
    else:
        print(f"   ❌ No valid {energy_label} k-factor calculations possible")
        return None


def generate_markdown_table(one_kev_results, five_kev_results, one_kev_regions, five_kev_regions):
    """Generate markdown table for k-factor comparison."""

    # Create output directory
    os.makedirs("results", exist_ok=True)

    # Generate markdown content
    markdown_content = "# K-Factor Comparison Table: 1keV vs 5keV\n\n"
    markdown_content += "## Side-by-Side K-Factor Analysis\n\n"

    # Main comparison table
    markdown_content += "| Parameter | 1keV | 5keV |\n"
    markdown_content += "|-----------|------|------|\n"

    # K-factor values
    markdown_content += f"| **Mean K-Factor (eV/V)** | **{one_kev_results['mean_k_factor']:.2f}** | **{five_kev_results['mean_k_factor']:.2f}** |\n"
    markdown_content += f"| Std Deviation (eV/V) | {one_kev_results['std_k_factor']:.3f} | {five_kev_results['std_k_factor']:.3f} |\n"
    markdown_content += f"| Min K-Factor (eV/V) | {one_kev_results['min_k_factor']:.2f} | {five_kev_results['min_k_factor']:.2f} |\n"
    markdown_content += f"| Max K-Factor (eV/V) | {one_kev_results['max_k_factor']:.2f} | {five_kev_results['max_k_factor']:.2f} |\n"
    markdown_content += f"| Number of Measurements | {len(one_kev_results['measurements'])} | {len(five_kev_results['measurements'])} |\n"

    # ESA voltage information
    one_kev_voltages = set(r.esa_voltage for r in one_kev_regions)
    five_kev_voltages = set(r.esa_voltage for r in five_kev_regions)

    one_kev_voltage_str = ', '.join(f'{v:.0f}V' for v in sorted(one_kev_voltages))
    five_kev_voltage_str = ', '.join(f'{v:.0f}V' for v in sorted(five_kev_voltages))

    markdown_content += f"| ESA Voltages | {one_kev_voltage_str} | {five_kev_voltage_str} |\n"

    # Expected k-factors
    one_kev_expected = [1000 / abs(v) for v in one_kev_voltages]
    five_kev_expected = [5000 / abs(v) for v in five_kev_voltages]

    markdown_content += f"| Expected K-Factor (eV/V) | {np.mean(one_kev_expected):.2f} | {np.mean(five_kev_expected):.2f} |\n"

    # Consistency analysis
    one_kev_consistency = one_kev_results['std_k_factor'] / one_kev_results['mean_k_factor'] * 100
    five_kev_consistency = five_kev_results['std_k_factor'] / five_kev_results['mean_k_factor'] * 100

    markdown_content += f"| Relative Std Dev (%) | {one_kev_consistency:.1f}% | {five_kev_consistency:.1f}% |\n"

    # Analysis section
    markdown_content += "\n## Analysis Summary\n\n"

    # K-factor comparison
    k_factor_ratio = five_kev_results['mean_k_factor'] / one_kev_results['mean_k_factor']
    expected_ratio = 5000 / 1000  # Should be 5.0 if voltages are the same

    markdown_content += f"### K-Factor Ratio Analysis\n"
    markdown_content += f"- **K-factor ratio (5keV/1keV)**: {k_factor_ratio:.2f}\n"
    markdown_content += f"- **Expected ratio (if same voltage)**: {expected_ratio:.1f}\n"

    if abs(k_factor_ratio - expected_ratio) < 0.5:
        markdown_content += f"- ✅ **Result**: K-factor ratio is close to expected energy ratio\n"
    else:
        markdown_content += f"- ⚠️ **Result**: K-factor ratio differs from energy ratio (different ESA voltages used)\n"

    # Consistency analysis
    markdown_content += f"\n### Consistency Analysis\n"
    if one_kev_consistency < 5 and five_kev_consistency < 5:
        markdown_content += f"- ✅ **Excellent consistency**: Both energies show <5% relative standard deviation\n"
    elif one_kev_consistency < 10 and five_kev_consistency < 10:
        markdown_content += f"- ✅ **Good consistency**: Both energies show <10% relative standard deviation\n"
    else:
        markdown_content += f"- ⚠️ **Poor consistency**: One or both energies show >10% relative standard deviation\n"

    # Voltage analysis
    markdown_content += f"\n### ESA Voltage Configuration\n"
    if one_kev_voltages == five_kev_voltages:
        markdown_content += f"- ✅ **Same ESA voltages** used for both energies\n"
    else:
        markdown_content += f"- ⚠️ **Different ESA voltages** used:\n"
        markdown_content += f"  - **1keV**: {one_kev_voltage_str}\n"
        markdown_content += f"  - **5keV**: {five_kev_voltage_str}\n"

    # Individual measurements table
    markdown_content += "\n## Individual Measurements\n\n"

    # 1keV measurements
    markdown_content += "### 1keV Measurements\n\n"
    markdown_content += "| # | Filename | Energy (eV) | ESA Voltage (V) | K-Factor (eV/V) |\n"
    markdown_content += "|---|----------|-------------|-----------------|------------------|\n"

    for i, measurement in enumerate(one_kev_results['measurements']):
        region = measurement.impact_region
        markdown_content += f"| {i+1} | `{region.filename}` | {region.beam_energy:.0f} | {region.esa_voltage:.0f} | {measurement.k_factor_estimate:.2f} |\n"

    # 5keV measurements
    markdown_content += "\n### 5keV Measurements\n\n"
    markdown_content += "| # | Filename | Energy (eV) | ESA Voltage (V) | K-Factor (eV/V) |\n"
    markdown_content += "|---|----------|-------------|-----------------|------------------|\n"

    for i, measurement in enumerate(five_kev_results['measurements']):
        region = measurement.impact_region
        markdown_content += f"| {i+1} | `{region.filename}` | {region.beam_energy:.0f} | {region.esa_voltage:.0f} | {measurement.k_factor_estimate:.2f} |\n"

    # Formula reference
    markdown_content += "\n## K-Factor Formula\n\n"
    markdown_content += "**K-Factor = Beam Energy (eV) / |ESA Voltage (V)|**\n\n"
    markdown_content += "This corrected formula properly accounts for the relationship between beam energy and ESA deflection voltage.\n"

    # Save markdown file
    output_path = "results/k_factor_comparison_table.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"✅ Markdown table saved: {output_path}")

    # Also print the main table to console
    print(f"\n📊 Markdown Table Generated:")
    print(f"| Parameter | 1keV | 5keV |")
    print(f"|-----------|------|------|")
    print(f"| **Mean K-Factor (eV/V)** | **{one_kev_results['mean_k_factor']:.2f}** | **{five_kev_results['mean_k_factor']:.2f}** |")
    print(f"| Std Deviation (eV/V) | {one_kev_results['std_k_factor']:.3f} | {five_kev_results['std_k_factor']:.3f} |")
    print(f"| Min K-Factor (eV/V) | {one_kev_results['min_k_factor']:.2f} | {five_kev_results['min_k_factor']:.2f} |")
    print(f"| Max K-Factor (eV/V) | {one_kev_results['max_k_factor']:.2f} | {five_kev_results['max_k_factor']:.2f} |")
    print(f"| Number of Measurements | {len(one_kev_results['measurements'])} | {len(five_kev_results['measurements'])} |")
    print(f"| ESA Voltages | {one_kev_voltage_str} | {five_kev_voltage_str} |")
    print(f"| Expected K-Factor (eV/V) | {np.mean(one_kev_expected):.2f} | {np.mean(five_kev_expected):.2f} |")
    print(f"| Relative Std Dev (%) | {one_kev_consistency:.1f}% | {five_kev_consistency:.1f}% |")

def compare_k_factors():
    """Compare k-factors side-by-side for 1keV and 5keV beam energies."""
    
    print("⚖️  Side-by-Side K-Factor Comparison: 1keV vs 5keV")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = ESAAnalyzer("data")
    data_manager = DataManager("data")
    all_files = data_manager.discover_files()
    
    # Separate files by beam energy
    one_kev_files = []
    five_kev_files = []
    
    for f in all_files:
        if (f.is_fits_or_map and 
            f.parameters.beam_energy_value and 
            f.parameters.esa_voltage_value is not None):
            
            energy = f.parameters.beam_energy_value
            if abs(energy - 1000) < 100:
                one_kev_files.append(f)
            elif abs(energy - 5000) < 100:
                five_kev_files.append(f)
    
    print(f"📁 File Summary:")
    print(f"   1keV files with ESA parameters: {len(one_kev_files)}")
    print(f"   5keV files with ESA parameters: {len(five_kev_files)}")
    
    # Analyze 1keV k-factors
    print(f"\n🔬 Analyzing 1keV K-Factors...")
    one_kev_results = None
    one_kev_regions = []
    
    if one_kev_files:
        try:
            one_kev_regions = analyzer.analyze_impact_regions(one_kev_files)
            print(f"   Found {len(one_kev_regions)} 1keV impact regions")
            
            if one_kev_regions:
                one_kev_results = analyzer.estimate_k_factor(one_kev_regions)
                if one_kev_results and one_kev_results.get('mean_k_factor'):
                    print(f"   ✅ 1keV k-factor: {one_kev_results['mean_k_factor']:.2f} ± {one_kev_results['std_k_factor']:.3f} eV/V")
                else:
                    print(f"   ❌ 1keV k-factor estimation failed")
                    # Calculate manually
                    one_kev_results = calculate_manual_k_factor(one_kev_regions, "1keV")
            else:
                print(f"   ❌ No 1keV impact regions found")
        except Exception as e:
            print(f"   ❌ Error analyzing 1keV: {e}")
    else:
        print(f"   ❌ No 1keV files found")
    
    # Analyze 5keV k-factors
    print(f"\n🔬 Analyzing 5keV K-Factors...")
    five_kev_results = None
    five_kev_regions = []
    
    if five_kev_files:
        try:
            five_kev_regions = analyzer.analyze_impact_regions(five_kev_files)
            print(f"   Found {len(five_kev_regions)} 5keV impact regions")
            
            if five_kev_regions:
                five_kev_results = analyzer.estimate_k_factor(five_kev_regions)
                if five_kev_results and five_kev_results.get('mean_k_factor'):
                    print(f"   ✅ 5keV k-factor: {five_kev_results['mean_k_factor']:.2f} ± {five_kev_results['std_k_factor']:.3f} eV/V")
                else:
                    print(f"   ❌ 5keV k-factor estimation failed")
                    # Calculate manually
                    five_kev_results = calculate_manual_k_factor(five_kev_regions, "5keV")
            else:
                print(f"   ❌ No 5keV impact regions found")
        except Exception as e:
            print(f"   ❌ Error analyzing 5keV: {e}")
    else:
        print(f"   ❌ No 5keV files found")
    
    # Side-by-side comparison
    print(f"\n📊 Side-by-Side K-Factor Comparison:")
    print(f"=" * 60)

    if one_kev_results and five_kev_results:
        # Generate markdown table
        generate_markdown_table(one_kev_results, five_kev_results, one_kev_regions, five_kev_regions)

        # Also print console version for immediate viewing
        print(f"\n📋 Console Summary:")
        print(f"{'Parameter':<25} {'1keV':<20} {'5keV':<20}")
        print(f"{'-'*25} {'-'*20} {'-'*20}")

        # K-factor values
        print(f"{'Mean K-Factor (eV/V)':<25} {one_kev_results['mean_k_factor']:<20.2f} {five_kev_results['mean_k_factor']:<20.2f}")
        print(f"{'Std Deviation (eV/V)':<25} {one_kev_results['std_k_factor']:<20.3f} {five_kev_results['std_k_factor']:<20.3f}")
        print(f"{'Min K-Factor (eV/V)':<25} {one_kev_results['min_k_factor']:<20.2f} {five_kev_results['min_k_factor']:<20.2f}")
        print(f"{'Max K-Factor (eV/V)':<25} {one_kev_results['max_k_factor']:<20.2f} {five_kev_results['max_k_factor']:<20.2f}")
        print(f"{'Number of Measurements':<25} {len(one_kev_results['measurements']):<20} {len(five_kev_results['measurements']):<20}")

        # ESA voltage information
        one_kev_voltages = set(r.esa_voltage for r in one_kev_regions)
        five_kev_voltages = set(r.esa_voltage for r in five_kev_regions)

        print(f"{'ESA Voltages (V)':<25} {', '.join(f'{v:.0f}' for v in sorted(one_kev_voltages)):<20} {', '.join(f'{v:.0f}' for v in sorted(five_kev_voltages)):<20}")

        # Expected k-factors
        one_kev_expected = [1000 / abs(v) for v in one_kev_voltages]
        five_kev_expected = [5000 / abs(v) for v in five_kev_voltages]

        print(f"{'Expected K-Factor':<25} {np.mean(one_kev_expected):<20.2f} {np.mean(five_kev_expected):<20.2f}")

        # Consistency analysis
        one_kev_consistency = one_kev_results['std_k_factor'] / one_kev_results['mean_k_factor'] * 100
        five_kev_consistency = five_kev_results['std_k_factor'] / five_kev_results['mean_k_factor'] * 100

        print(f"{'Relative Std Dev (%)':<25} {one_kev_consistency:<20.1f} {five_kev_consistency:<20.1f}")
        
        # Analysis
        print(f"\n🔍 Analysis:")
        
        # K-factor comparison
        k_factor_ratio = five_kev_results['mean_k_factor'] / one_kev_results['mean_k_factor']
        expected_ratio = 5000 / 1000  # Should be 5.0 if voltages are the same
        
        print(f"   K-factor ratio (5keV/1keV): {k_factor_ratio:.2f}")
        print(f"   Expected ratio (if same voltage): {expected_ratio:.1f}")
        
        if abs(k_factor_ratio - expected_ratio) < 0.5:
            print(f"   ✅ K-factor ratio is close to expected energy ratio")
        else:
            print(f"   ⚠️  K-factor ratio differs from energy ratio (different ESA voltages)")
        
        # Consistency comparison
        if one_kev_consistency < 5 and five_kev_consistency < 5:
            print(f"   ✅ Both energies show excellent consistency (<5% relative std dev)")
        elif one_kev_consistency < 10 and five_kev_consistency < 10:
            print(f"   ✅ Both energies show good consistency (<10% relative std dev)")
        else:
            print(f"   ⚠️  One or both energies show poor consistency (>10% relative std dev)")
        
        # Voltage analysis
        if one_kev_voltages == five_kev_voltages:
            print(f"   ✅ Same ESA voltages used for both energies")
        else:
            print(f"   ⚠️  Different ESA voltages used:")
            print(f"      1keV: {sorted(one_kev_voltages)} V")
            print(f"      5keV: {sorted(five_kev_voltages)} V")
    
    else:
        if not one_kev_results:
            print(f"{'1keV Analysis':<25} {'FAILED':<20} {'-':<20}")
        if not five_kev_results:
            print(f"{'5keV Analysis':<25} {'-':<20} {'FAILED':<20}")
    
    # Create comparison plot
    if one_kev_results and five_kev_results:
        print(f"\n📈 Creating comparison plot...")
        create_k_factor_comparison_plot(one_kev_results, five_kev_results, one_kev_regions, five_kev_regions)
    
    # Individual measurement details
    print(f"\n📋 Individual Measurements:")
    
    if one_kev_results and one_kev_results.get('measurements'):
        print(f"\n   1keV Measurements:")
        for i, measurement in enumerate(one_kev_results['measurements']):
            region = measurement.impact_region
            print(f"   {i+1}. {region.filename}")
            print(f"      Energy: {region.beam_energy:.0f} eV, ESA: {region.esa_voltage:.0f} V")
            print(f"      K-factor: {region.beam_energy:.0f} / {abs(region.esa_voltage):.0f} = {measurement.k_factor_estimate:.2f} eV/V")
    
    if five_kev_results and five_kev_results.get('measurements'):
        print(f"\n   5keV Measurements:")
        for i, measurement in enumerate(five_kev_results['measurements']):
            region = measurement.impact_region
            print(f"   {i+1}. {region.filename}")
            print(f"      Energy: {region.beam_energy:.0f} eV, ESA: {region.esa_voltage:.0f} V")
            print(f"      K-factor: {region.beam_energy:.0f} / {abs(region.esa_voltage):.0f} = {measurement.k_factor_estimate:.2f} eV/V")
    
    print(f"\n✅ Side-by-side k-factor comparison complete!")


def create_k_factor_comparison_plot(one_kev_results, five_kev_results, one_kev_regions, five_kev_regions):
    """Create a comparison plot of k-factors for both energies."""
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Extract k-factor values
    one_kev_k_factors = [m.k_factor_estimate for m in one_kev_results['measurements'] if m.k_factor_estimate]
    five_kev_k_factors = [m.k_factor_estimate for m in five_kev_results['measurements'] if m.k_factor_estimate]
    
    # Plot 1: K-factor comparison bar chart
    energies = ['1keV', '5keV']
    means = [one_kev_results['mean_k_factor'], five_kev_results['mean_k_factor']]
    stds = [one_kev_results['std_k_factor'], five_kev_results['std_k_factor']]
    
    bars = axes[0, 0].bar(energies, means, yerr=stds, capsize=5, alpha=0.7, 
                         color=['skyblue', 'lightcoral'])
    axes[0, 0].set_ylabel('K-Factor (eV/V)')
    axes[0, 0].set_title('K-Factor Comparison: 1keV vs 5keV')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, mean, std in zip(bars, means, stds):
        height = bar.get_height()
        axes[0, 0].text(bar.get_x() + bar.get_width()/2., height + std + 0.1,
                       f'{mean:.2f} ± {std:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # Plot 2: K-factor distribution histograms
    axes[0, 1].hist(one_kev_k_factors, bins=10, alpha=0.7, label='1keV', color='skyblue')
    axes[0, 1].hist(five_kev_k_factors, bins=10, alpha=0.7, label='5keV', color='lightcoral')
    axes[0, 1].set_xlabel('K-Factor (eV/V)')
    axes[0, 1].set_ylabel('Number of Measurements')
    axes[0, 1].set_title('K-Factor Distribution')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: ESA voltage vs K-factor
    one_kev_voltages = [abs(r.esa_voltage) for r in one_kev_regions]
    five_kev_voltages = [abs(r.esa_voltage) for r in five_kev_regions]
    
    axes[1, 0].scatter(one_kev_voltages, one_kev_k_factors, alpha=0.7, s=50, 
                      label='1keV', color='skyblue')
    axes[1, 0].scatter(five_kev_voltages, five_kev_k_factors, alpha=0.7, s=50, 
                      label='5keV', color='lightcoral')
    axes[1, 0].set_xlabel('ESA Voltage (V)')
    axes[1, 0].set_ylabel('K-Factor (eV/V)')
    axes[1, 0].set_title('K-Factor vs ESA Voltage')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Expected vs measured k-factors
    one_kev_expected = [1000 / abs(r.esa_voltage) for r in one_kev_regions]
    five_kev_expected = [5000 / abs(r.esa_voltage) for r in five_kev_regions]
    
    # Perfect correlation line
    all_expected = one_kev_expected + five_kev_expected
    all_measured = one_kev_k_factors + five_kev_k_factors
    min_val = min(min(all_expected), min(all_measured))
    max_val = max(max(all_expected), max(all_measured))
    
    axes[1, 1].plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='Perfect correlation')
    axes[1, 1].scatter(one_kev_expected, one_kev_k_factors, alpha=0.7, s=50, 
                      label='1keV', color='skyblue')
    axes[1, 1].scatter(five_kev_expected, five_kev_k_factors, alpha=0.7, s=50, 
                      label='5keV', color='lightcoral')
    axes[1, 1].set_xlabel('Expected K-Factor (eV/V)')
    axes[1, 1].set_ylabel('Measured K-Factor (eV/V)')
    axes[1, 1].set_title('Expected vs Measured K-Factor')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    # Overall title
    fig.suptitle('ESA K-Factor Analysis: 1keV vs 5keV Beam Energy Comparison', 
                fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    
    # Save plot
    os.makedirs("results", exist_ok=True)
    save_path = "results/k_factor_comparison_1keV_vs_5keV.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"   📊 Comparison plot saved: {save_path}")
    
    plt.show()


if __name__ == "__main__":
    compare_k_factors()
