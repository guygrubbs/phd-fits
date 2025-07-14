# XDL Processing - Complete Usage Guide

## 🎯 **Getting Started**

### **Prerequisites**
- Python 3.7+
- Required packages: numpy, matplotlib, astropy, pandas
- Data files in `data/` directory (FITS, MAP, or PHD files)

### **Installation**
```bash
# Clone or download the XDL Processing project
cd "XDL Processing"

# Verify data directory exists
ls data/

# Test basic functionality
python test_esa_analysis.py
```

## 🚀 **Quick Analysis Workflows**

### **Complete Analysis (Recommended)**
```bash
# 1. Overview of available data
python integrated_map_tool.py --list-only

# 2. K-factor verification
python test_esa_analysis.py

# 3. Complete detector response map
python integrated_map_tool.py --beam-energy 1000

# 4. Angular response analysis  
python elevation_azimuth_tool.py --beam-energy 1000

# 5. Resolution analysis
python angular_resolution_tool.py --beam-energy 1000

# 6. Enhanced spatial mapping
python enhanced_map_plot.py --mode auto
```

### **Essential Analysis (3 Commands)**
```bash
python test_esa_analysis.py                           # K-factor: 5.45 ± 0.06 eV/V
python integrated_map_tool.py --beam-energy 1000      # Complete detector response
python elevation_azimuth_tool.py --beam-energy 1000   # Angular mapping
```

### **Data Exploration**
```bash
# See what's available for each analysis type
python integrated_map_tool.py --list-only
python elevation_azimuth_tool.py --list-only  
python angular_resolution_tool.py --list-only
```

## 📊 **Tool-Specific Usage**

### **1. Integrated Count Rate Maps**
**Purpose**: Create unified detector response map from all measurements

```bash
# Basic usage
python integrated_map_tool.py --beam-energy 1000

# Custom target rate
python integrated_map_tool.py --beam-energy 1000 --target-rate 50

# All beam energies
python integrated_map_tool.py --target-rate 100

# List available data
python integrated_map_tool.py --list-only
```

**Output**: 
- `results/integrated_count_rate_map_E1000eV_rate100.png` (4-panel log-scale plot)
- `results/integrated_map_analysis_E1000eV_rate100.md` (detailed report)

**Features**:
- ✅ Rate normalization to common baseline (default: 100 counts/s)
- ✅ Enhanced log scale visualization for impact visibility
- ✅ Pixel-by-pixel integration across all measurements
- ✅ Contour lines highlighting impact boundaries

### **2. Elevation vs Azimuth Analysis**
**Purpose**: Angular response mapping with rate normalization

```bash
# Count rate analysis
python elevation_azimuth_tool.py --beam-energy 1000 --plot-type count_rate

# Normalized intensity
python elevation_azimuth_tool.py --beam-energy 1000 --plot-type normalized_intensity

# Total counts (no rate normalization)
python elevation_azimuth_tool.py --beam-energy 1000 --plot-type total_counts

# List available datasets
python elevation_azimuth_tool.py --list-only
```

**Output**:
- `results/elevation_azimuth_E1000eV_count_rate.png` (4-panel angular plot)
- `results/elevation_azimuth_E1000eV.md` (measurement details)

**Features**:
- ✅ Collection time estimation based on signal characteristics
- ✅ Count rate calculation (counts per second)
- ✅ 4-panel visualization: elevation/azimuth, spatial, rates, quality
- ✅ Angular coordinate mapping (elevation = inner angle, azimuth = horizontal)

### **3. Angular Resolution Analysis**
**Purpose**: Resolution plots when beam energy and one angle are constant

```bash
# Basic resolution analysis
python angular_resolution_tool.py --beam-energy 1000

# Custom thresholds
python angular_resolution_tool.py --beam-energy 1000 --min-voltages 2 --min-angles 1

# Specific fixed angle
python angular_resolution_tool.py --beam-energy 1000 --fixed-angle 62

# List potential datasets
python angular_resolution_tool.py --list-only
```

**Output**:
- `results/angular_resolution_E1000eV_A62deg.png` (resolution analysis)
- `results/angular_resolution_E1000eV_A62deg.md` (detailed measurements)

**Features**:
- ✅ Handles constant angle parameters (missing = assumed constant)
- ✅ Voltage sweep analysis when angles are fixed
- ✅ 2D resolution maps when both angles and voltages vary
- ✅ K-factor consistency verification

### **4. K-Factor Analysis**
**Purpose**: ESA performance verification with correct formula

```bash
# Quick k-factor test
python test_esa_analysis.py

# Full ESA analysis with spatial mapping
python esa_mapping_analysis.py

# Enhanced mapping
python enhanced_map_plot.py --mode auto
```

**Output**: Console output with k-factor statistics and file analysis

**Features**:
- ✅ Correct k-factor formula: K = Beam Energy (eV) / |ESA Voltage (V)|
- ✅ Angle range support (e.g., "84to-118" degrees)
- ✅ Statistical analysis with uncertainty estimates
- ✅ Individual measurement breakdown

### **5. Enhanced Mapping**
**Purpose**: Advanced spatial visualization with normalization options

```bash
# Automatic mode (local normalization)
python enhanced_map_plot.py --mode auto

# Local normalization (default)
python enhanced_map_plot.py --mode local

# Global normalization
python enhanced_map_plot.py --mode global

# Specific beam energy
python enhanced_map_plot.py --mode auto --beam-energy 1000
```

**Output**: 
- `results/spatial_mapping_by_energy.png` (enhanced spatial plots)
- Various analysis reports

**Features**:
- ✅ Local normalization for temporal visibility (default)
- ✅ Global normalization for absolute comparison
- ✅ Qualitative spatial description
- ✅ Multiple visualization modes

## 📁 **Understanding Output Files**

### **Plot Files (PNG)**
- **Integrated maps**: `integrated_count_rate_map_E{energy}eV_rate{rate}.png`
- **Angular analysis**: `elevation_azimuth_E{energy}eV_count_rate.png`
- **Resolution plots**: `angular_resolution_E{energy}eV_A{angle}deg.png`
- **Enhanced mapping**: `spatial_mapping_by_energy.png`

### **Report Files (Markdown)**
- **Integration details**: `integrated_map_analysis_E{energy}eV_rate{rate}.md`
- **Angular measurements**: `elevation_azimuth_E{energy}eV.md`
- **Resolution analysis**: `angular_resolution_E{energy}eV_A{angle}deg.md`
- **Comparative analysis**: `comparative_analysis_report.md`

## 🔧 **Advanced Options**

### **Custom Data Directory**
```bash
python integrated_map_tool.py --data-dir /path/to/data --output-dir /path/to/results
```

### **Filtering by Parameters**
```bash
# Specific beam energy
python elevation_azimuth_tool.py --beam-energy 1000

# Custom rate normalization
python integrated_map_tool.py --target-rate 50

# Minimum data requirements
python angular_resolution_tool.py --min-voltages 3 --min-angles 2
```

### **Analysis Modes**
```bash
# Different plot types
python elevation_azimuth_tool.py --plot-type count_rate        # Recommended
python elevation_azimuth_tool.py --plot-type normalized_intensity
python elevation_azimuth_tool.py --plot-type total_counts

# Different normalization modes
python enhanced_map_plot.py --mode local    # Default, temporal visibility
python enhanced_map_plot.py --mode global   # Absolute comparison
python enhanced_map_plot.py --mode auto     # Automatic selection
```

## 🎯 **Workflow Recommendations**

### **First-Time Analysis**
1. **Data exploration**: `python integrated_map_tool.py --list-only`
2. **K-factor verification**: `python test_esa_analysis.py`
3. **Complete detector map**: `python integrated_map_tool.py --beam-energy 1000`
4. **Angular analysis**: `python elevation_azimuth_tool.py --beam-energy 1000`

### **Regular Analysis**
1. **Integrated mapping**: Primary analysis for complete detector response
2. **Angular mapping**: Understanding beam behavior vs angles
3. **Resolution analysis**: When parameter variations are systematic

### **Troubleshooting**
1. **No data found**: Check `--list-only` options to see available datasets
2. **Empty results**: Verify beam energy values match your data
3. **Missing plots**: Check `results/` directory permissions
4. **Rate issues**: Adjust `--target-rate` for better normalization

## ✅ **Key Features Summary**

- **Rate Normalization**: All tools account for varying data collection rates
- **Log Scale Visualization**: Enhanced visibility across wide dynamic ranges
- **Angle Range Support**: Handles files with rotation ranges automatically
- **Constant Parameter Handling**: Missing angles assumed constant
- **Quality Filtering**: Automatic exclusion of empty/corrupted files
- **Comprehensive Reporting**: Both visual plots and detailed analysis reports
- **Flexible Input**: Works with various filename conventions and data formats

The XDL Processing toolkit provides complete analysis capabilities for ESA experimental data with proper scientific rigor and user-friendly interfaces!
