# XDL Processing Tools Documentation

## 📋 **Overview**

The XDL Processing project provides a comprehensive suite of analysis tools for processing experimental data from electrostatic analyzer (ESA) systems. All tools support rate normalization, handle angle ranges, and provide both visualization and detailed reporting.

## 🛠️ **Available Analysis Tools**

### **1. ESA Analysis & K-Factor Estimation**
**Purpose**: Analyze ESA performance and calculate k-factors with proper formula (K = E_beam/V_esa)

**Tools**:
- `src/esa_analysis.py` - Core ESA analysis module
- `esa_mapping_analysis.py` - ESA mapping with spatial analysis
- `test_esa_analysis.py` - Quick k-factor testing

**Key Features**:
- ✅ Correct k-factor formula: K = Beam Energy (eV) / |ESA Voltage (V)|
- ✅ Angle range support (e.g., "84to-118" degrees)
- ✅ Spatial impact region analysis
- ✅ Statistical analysis with uncertainty estimates

### **2. Angular Resolution Analysis**
**Purpose**: Create elevation/azimuth resolution plots when beam energy and one angle are constant while ESA voltage and another angle vary

**Tools**:
- `src/angular_resolution_analysis.py` - Core angular resolution module
- `angular_resolution_tool.py` - Command-line interface
- `test_angular_resolution.py` - Testing and validation

**Key Features**:
- ✅ Handles constant angle parameters (missing = assumed constant)
- ✅ 2D resolution mapping
- ✅ Voltage sweep analysis
- ✅ K-factor consistency verification

### **3. Elevation vs Azimuth Analysis**
**Purpose**: Create elevation vs azimuth plots with rate normalization for varying data collection rates

**Tools**:
- `src/elevation_azimuth_analysis.py` - Core elevation/azimuth module
- `elevation_azimuth_tool.py` - Command-line interface

**Key Features**:
- ✅ Rate normalization (counts per second)
- ✅ Collection time estimation
- ✅ 4-panel visualization (elevation/azimuth, spatial, rates, quality)
- ✅ Angular coordinate mapping

### **4. Integrated Count Rate Maps**
**Purpose**: Normalize each map file to common count rate and sum all data collection periods for comprehensive detector response

**Tools**:
- `src/integrated_map_analysis.py` - Core integration module
- `integrated_map_tool.py` - Command-line interface
- `test_integrated_log_scale.py` - Log scale testing

**Key Features**:
- ✅ Enhanced log scale visualization for impact visibility
- ✅ Rate normalization to common baseline
- ✅ Pixel-by-pixel integration across all measurements
- ✅ Contour lines for impact boundary detection

### **5. Enhanced Map Plotting**
**Purpose**: Advanced spatial mapping with local normalization options

**Tools**:
- `enhanced_map_plot.py` - Enhanced mapping with multiple modes
- `src/enhanced_mapping.py` - Core enhanced mapping module

**Key Features**:
- ✅ Local normalization (default for temporal visibility)
- ✅ Global normalization option
- ✅ Multiple visualization modes
- ✅ Qualitative spatial description

## 🚀 **Command-Line Usage Guide**

### **Quick Analysis Commands**

#### **K-Factor Analysis**
```bash
# Quick k-factor test with corrected formula
python test_esa_analysis.py

# Full ESA analysis with spatial mapping
python esa_mapping_analysis.py

# Enhanced mapping with local normalization
python enhanced_map_plot.py --mode auto
```

#### **Angular Resolution Analysis**
```bash
# List available angular resolution datasets
python angular_resolution_tool.py --list-only

# Analyze specific beam energy
python angular_resolution_tool.py --beam-energy 1000

# Custom thresholds
python angular_resolution_tool.py --min-voltages 2 --min-angles 1
```

#### **Elevation vs Azimuth Analysis**
```bash
# List available datasets
python elevation_azimuth_tool.py --list-only

# Generate count rate plot
python elevation_azimuth_tool.py --beam-energy 1000 --plot-type count_rate

# Generate normalized intensity plot
python elevation_azimuth_tool.py --beam-energy 1000 --plot-type normalized_intensity
```

#### **Integrated Count Rate Maps**
```bash
# List available map files
python integrated_map_tool.py --list-only

# Create integrated map (default 100 counts/s normalization)
python integrated_map_tool.py --beam-energy 1000

# Custom target rate
python integrated_map_tool.py --beam-energy 1000 --target-rate 50
```

### **Advanced Usage Options**

#### **Angular Resolution Tool**
```bash
python angular_resolution_tool.py [OPTIONS]

Options:
  --data-dir PATH          Data directory path (default: data)
  --output-dir PATH        Output directory path (default: results)
  --beam-energy FLOAT      Specific beam energy to analyze (eV)
  --fixed-angle FLOAT      Specific angle to hold constant (degrees)
  --min-voltages INT       Minimum ESA voltage points required (default: 2)
  --min-angles INT         Minimum angle variations required (default: 1)
  --list-only             Only list datasets without analysis
```

#### **Elevation/Azimuth Tool**
```bash
python elevation_azimuth_tool.py [OPTIONS]

Options:
  --data-dir PATH          Data directory path (default: data)
  --output-dir PATH        Output directory path (default: results)
  --beam-energy FLOAT      Specific beam energy to analyze (eV)
  --plot-type CHOICE       Type of plot: count_rate, normalized_intensity, total_counts
  --list-only             Only list datasets without analysis
```

#### **Integrated Map Tool**
```bash
python integrated_map_tool.py [OPTIONS]

Options:
  --data-dir PATH          Data directory path (default: data)
  --output-dir PATH        Output directory path (default: results)
  --beam-energy FLOAT      Specific beam energy to analyze (eV)
  --target-rate FLOAT      Target count rate for normalization (default: 100.0)
  --list-only             Only list map files without analysis
```

#### **Enhanced Map Plot**
```bash
python enhanced_map_plot.py [OPTIONS]

Options:
  --mode CHOICE           Normalization mode: auto, local, global
  --beam-energy FLOAT     Specific beam energy to analyze
  --output-dir PATH       Output directory path
```

## 📊 **Output Files Generated**

### **Plot Files (PNG)**
- `angular_resolution_E{energy}eV_A{angle}deg.png` - Angular resolution analysis
- `elevation_azimuth_E{energy}eV_count_rate.png` - Elevation vs azimuth plots
- `integrated_count_rate_map_E{energy}eV_rate{rate}.png` - Integrated maps
- `spatial_mapping_by_energy.png` - Enhanced spatial mapping
- `comparative_analysis_report.png` - Comparative analysis plots

### **Report Files (Markdown)**
- `angular_resolution_E{energy}eV_A{angle}deg.md` - Detailed angular analysis
- `elevation_azimuth_E{energy}eV.md` - Elevation/azimuth measurements
- `integrated_map_analysis_E{energy}eV_rate{rate}.md` - Integration details
- `comparative_analysis_report.md` - Cross-analysis comparison

## 🔧 **Core Modules**

### **Data Handling**
- `src/data_model.py` - Core data structures and file discovery
- `src/fits_handler.py` - FITS file reading and processing
- `src/parameter_parser.py` - Filename parameter extraction

### **Analysis Engines**
- `src/esa_analysis.py` - ESA analysis and k-factor calculations
- `src/angular_resolution_analysis.py` - Angular resolution analysis
- `src/elevation_azimuth_analysis.py` - Elevation/azimuth analysis
- `src/integrated_map_analysis.py` - Integrated mapping analysis
- `src/enhanced_mapping.py` - Enhanced spatial mapping

## 🎯 **Workflow Recommendations**

### **Complete Analysis Workflow**
```bash
# 1. Quick overview of available data
python integrated_map_tool.py --list-only
python elevation_azimuth_tool.py --list-only
python angular_resolution_tool.py --list-only

# 2. K-factor analysis
python test_esa_analysis.py

# 3. Comprehensive spatial analysis
python integrated_map_tool.py --beam-energy 1000

# 4. Angular response analysis
python elevation_azimuth_tool.py --beam-energy 1000 --plot-type count_rate

# 5. Resolution analysis
python angular_resolution_tool.py --beam-energy 1000

# 6. Enhanced mapping
python enhanced_map_plot.py --mode auto
```

### **Quick Analysis Workflow**
```bash
# Essential analysis in 3 commands
python test_esa_analysis.py                    # K-factor verification
python integrated_map_tool.py --beam-energy 1000  # Complete detector response
python elevation_azimuth_tool.py --beam-energy 1000  # Angular analysis
```

## 📁 **Directory Structure**
```
XDL Processing/
├── src/                    # Core analysis modules
├── data/                   # Experimental data files
├── results/                # Generated plots and reports
├── *_tool.py              # Command-line interfaces
├── test_*.py              # Testing and validation scripts
└── *.md                   # Documentation and summaries
```

## 🔍 **Data Requirements**

### **File Formats Supported**
- **FITS files**: Primary experimental data format
- **MAP files**: Alternative data format
- **Filename conventions**: Automatic parameter extraction

### **Required Parameters**
- **Beam Energy**: Must be specified in filename or header
- **ESA Voltage**: Required for k-factor and deflection analysis
- **Angular Information**: Inner angles, horizontal values (optional, assumed constant if missing)

### **Optional Parameters**
- **Collection Time**: Estimated if not in FITS header
- **Focus Positions**: Used for enhanced analysis
- **MCP Settings**: Detector configuration information

## ✅ **Key Features Across All Tools**

1. **Rate Normalization**: All tools account for varying data collection rates
2. **Angle Range Support**: Handles files with angle ranges (e.g., "84to-118")
3. **Constant Parameter Handling**: Missing angles assumed constant
4. **Quality Filtering**: Automatic exclusion of empty/corrupted files
5. **Log Scale Visualization**: Enhanced visibility for wide dynamic ranges
6. **Comprehensive Reporting**: Both visual plots and detailed markdown reports
7. **Flexible Input**: Works with various filename conventions and data formats

The XDL Processing toolkit provides complete analysis capabilities for ESA experimental data with proper rate normalization, spatial mapping, and comprehensive visualization!
