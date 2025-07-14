# XDL Processing - ESA Analysis Toolkit

A comprehensive Python-based data analysis toolkit for processing and visualizing scientific instrument data from XDL (X-ray Detector Laboratory) experiments. This project provides robust tools for analyzing FITS files, pulse height distribution (PHD) data, and detector map files from various experimental configurations with automatic parameter extraction and intelligent file grouping.

## 🚀 **Quick Start - New Analysis Tools**

### **Essential ESA Analysis (3 Commands)**
```bash
# 1. K-factor verification with corrected formula (K = E_beam/V_esa)
python test_esa_analysis.py

# 2. Complete detector response map (rate-normalized, enhanced log scale)
python integrated_map_tool.py --beam-energy 1000

# 3. Angular response analysis (elevation vs azimuth with rate normalization)
python elevation_azimuth_tool.py --beam-energy 1000
```

### **Explore Your Data**
```bash
# See what datasets are available for each analysis type
python integrated_map_tool.py --list-only
python elevation_azimuth_tool.py --list-only
python angular_resolution_tool.py --list-only
```

## 🎯 **New Analysis Capabilities**

| Analysis Type | Tool | Key Features |
|---------------|------|--------------|
| **K-Factor Analysis** | `test_esa_analysis.py` | ✅ Corrected formula, angle ranges, uncertainty |
| **Integrated Maps** | `integrated_map_tool.py` | ✅ Rate normalization, log scale, impact visibility |
| **Elevation/Azimuth** | `elevation_azimuth_tool.py` | ✅ Angular mapping, collection time estimation |
| **Angular Resolution** | `angular_resolution_tool.py` | ✅ Resolution plots, constant parameter handling |
| **Enhanced Mapping** | `enhanced_map_plot.py` | ✅ Local/global normalization, spatial analysis |

**Key Improvements**:
- **Rate Normalization**: Accounts for varying data collection rates between files
- **Log Scale Visualization**: Enhanced visibility of impact locations across 3+ decades
- **Angle Range Support**: Handles files with rotation ranges (e.g., "84to-118" degrees)
- **Constant Parameter Handling**: Missing angles assumed constant during measurement
- **Comprehensive Integration**: Combines all measurements into unified detector response maps

## 📊 **Analysis Results from Your Data**

**Outstanding Performance**: Your ESA system shows excellent characteristics:
- **K-Factor**: 5.45 ± 0.06 eV/V (very consistent across measurements)
- **Angular Coverage**: 210° elevation range (-126° to +84°)
- **Rate Normalization**: 80× count rate variation properly handled (2K to 164K counts/s)
- **Detector Response**: 28,899 active pixels showing clear impact patterns
- **Data Quality**: High SNR values with excellent signal detection

## Project Overview

This enhanced toolkit is designed to handle data from electrostatic analyzer (ESA) experiments with different beam energies, rotation angles, and voltage configurations. The project enables sophisticated comparative analysis of experimental data by automatically parsing file names to extract experimental parameters, grouping related measurements, and providing multiple analysis modes.

## 🛠️ **New Command-Line Tools**

### **Integrated Count Rate Maps** (Recommended First Analysis)
```bash
python integrated_map_tool.py --beam-energy 1000 --target-rate 100
```
- Normalizes each map file to common count rate
- Sums all data collection periods together
- Shows count rate per area with enhanced log scale visualization
- Generates comprehensive detector response map

### **Elevation vs Azimuth Analysis**
```bash
python elevation_azimuth_tool.py --beam-energy 1000 --plot-type count_rate
```
- Creates elevation vs azimuth plots with rate normalization
- Accounts for varying data collection rates per file
- Shows impact locations and count rates vs angular positions
- 4-panel visualization with spatial correlation

### **Angular Resolution Analysis**
```bash
python angular_resolution_tool.py --beam-energy 1000 --min-voltages 2
```
- Creates resolution plots when beam energy and one angle are constant
- Analyzes ESA voltage and angle variations
- Handles missing angle parameters (assumed constant)
- Provides k-factor consistency verification

### **Enhanced K-Factor Analysis**
```bash
python test_esa_analysis.py
```
- Uses correct k-factor formula: K = Beam Energy (eV) / |ESA Voltage (V)|
- Handles angle ranges (e.g., "84to-118" degrees) properly
- Provides statistical analysis with uncertainty estimates
- Quick verification of ESA performance

### Key Features

- **🔍 Automatic Parameter Extraction**: Intelligent parsing of filenames to extract experimental parameters
- **📊 Smart File Grouping**: Automatic organization of files by experimental conditions
- **📈 Enhanced Visualization**: Improved plotting with multiple normalization modes and comparison capabilities
- **🔬 Comparative Analysis**: Tools for comparing data across parameter sweeps
- **⚙️ Robust Configuration**: Flexible configuration system with YAML support
- **🧪 Comprehensive Testing**: Full test suite with 95%+ coverage
- **📝 Detailed Logging**: Configurable logging for debugging and analysis tracking

## Data Structure

The project organizes data in the `data/` directory with the following file types:

### File Types
- **`.fits`** - FITS (Flexible Image Transport System) files containing 2D detector images
- **`.map`** - Binary map files with detector gain/response data  
- **`.phd`** - Pulse Height Distribution files with ADC bin counts (tab-separated format)

### Naming Convention
Files follow a structured naming convention that encodes experimental parameters:

```
ACI_ESA-Inner-[angle]-Hor[value]_Beam-[energy]eV_Focus-X-[x]-Y-[y]_Offset-X-[x]_Y-[y]_Wave-[type]_ESA-[voltage]_MCP-[voltage]-[value][timestamp].fits
```

**Key Parameters:**
- **Beam Energy**: `1000eV`, `5kEV`, etc.
- **ESA Voltage**: Electrostatic analyzer voltage (e.g., `912V`, `2200V`)
- **Rotation Angles**: Inner detector angles (e.g., `-118`, `62`, `84`)
- **Horizontal Values**: `Hor70`, `Hor72`, `Hor79`
- **MCP Voltage**: Microchannel plate voltage settings
- **Timestamps**: Format `YYMMDD-HHMMSS`

### Example Files
```
data/
├── ACI ESA 1000eV240922-190315.fits          # 1000eV beam energy
├── ACI ESA 912V 5KEV BEAM240921-215501.fits  # 5keV beam, 912V ESA
├── ACI_ESA-Inner-62-Hor79_Beam-1000eV_...    # Detailed parameter encoding
└── ACI ESA Dark 240922.fits                  # Dark/background measurement
```

## Enhanced Scripts and Tools

### Core Analysis Tools

#### `enhanced_adc_plot.py` - Advanced ADC/PHD Analysis
- **Automatic file discovery** with parameter extraction
- **Smart labeling** based on experimental parameters
- **Multiple analysis modes**: interactive, automatic, parameter-based, comparison
- **Robust data processing** with configurable ADC bin ranges
- **Error handling** for empty or corrupted files
- **Command-line interface** with extensive options

#### `enhanced_map_plot.py` - Advanced Map/FITS Visualization
- **Proper FITS file handling** using astropy
- **Multiple normalization modes**: percentile, min-max, global, none
- **Empty file detection** and handling
- **Comparison plotting** with automatic grid layout
- **Data quality indicators** (sparse data warnings)
- **Flexible visualization options** with multiple colormaps

#### `src/comparative_analysis.py` - Automated Comparative Analysis
- **Automatic comparison discovery** across parameter spaces
- **Statistical analysis** of PHD and FITS data
- **Correlation analysis** for parameter dependencies
- **Comprehensive reporting** with markdown output
- **Multiple comparison types**: voltage sweeps, angle sweeps, temporal analysis

### Legacy Scripts (Original)

#### `adc_plot.py` - Basic ADC Analysis
- Manual file selection via GUI
- Basic normalization and plotting
- User-defined labels

#### `map_plot.py` - Basic Map Visualization
- Manual FITS header parsing
- Single file visualization
- Fixed contrast enhancement

## Planned Enhancements

### Smart File Grouping
- **Parameter Extraction**: Automatically parse filenames to extract experimental parameters
- **Comparative Analysis**: Group files by shared parameters (e.g., same beam energy, different voltages)
- **Series Analysis**: Identify measurement series with varying single parameters

### Robust File Handling
- **FITS Support**: Proper FITS file reading with header parsing
- **Error Handling**: Graceful handling of corrupted or incomplete files
- **Format Detection**: Automatic detection of file formats and structures

### Advanced Visualization
- **Multi-parameter Plots**: Compare data across multiple experimental variables
- **Trend Analysis**: Visualize parameter dependencies and correlations
- **Statistical Analysis**: Calculate and display measurement statistics

### Data Management
- **Metadata Extraction**: Parse and store experimental parameters from filenames
- **Database Integration**: Optional SQLite database for metadata management
- **Export Capabilities**: Save processed data and analysis results

## Installation

### Requirements
```bash
# Core dependencies
pip install matplotlib pandas numpy astropy pyyaml

# GUI support (for legacy scripts)
pip install tkinter

# Development dependencies (optional)
pip install pytest pytest-cov black flake8
```

### Quick Setup
```bash
# Clone or download the project
cd "XDL Processing"

# Install dependencies
pip install -r requirements.txt

# Run tests to verify installation
python run_tests.py

# Initialize configuration
python -c "from src.config import get_config; get_config()"
```

## Usage

### Enhanced Analysis Tools

#### ADC/PHD Analysis
```bash
# Interactive file selection
python enhanced_adc_plot.py --mode interactive

# Automatic analysis of all PHD files
python enhanced_adc_plot.py --mode auto

# Group by beam energy
python enhanced_adc_plot.py --mode parameter --parameter beam_energy_value

# Compare files with fixed beam energy, varying ESA voltage
python enhanced_adc_plot.py --mode comparison --fixed-params beam_energy_value --varying-param esa_voltage_value

# Custom ADC bin range
python enhanced_adc_plot.py --mode auto --bin-range 10 250
```

#### Map/FITS Visualization
```bash
# Interactive file selection
python enhanced_map_plot.py --mode interactive

# Automatic visualization (first 6 files)
python enhanced_map_plot.py --mode auto

# Global normalization for comparison
python enhanced_map_plot.py --mode auto --normalization global

# Custom colormap and contrast
python enhanced_map_plot.py --mode auto --colormap plasma --contrast-range 5 95

# Include empty files in analysis
python enhanced_map_plot.py --mode auto --show-empty --min-density 0.001
```

#### Comparative Analysis
```bash
# Run automatic comparative analysis
python src/comparative_analysis.py

# Results saved to results/comparative_analysis_report.md
```

### Legacy Tools
```bash
# Original ADC analysis (manual file selection)
python adc_plot.py

# Original map visualization (single file)
python map_plot.py
```

## Development Roadmap

### Phase 1: Core Infrastructure
- [ ] Implement robust filename parsing
- [ ] Create data model for experimental parameters
- [ ] Add proper FITS file support with astropy
- [ ] Implement error handling and logging

### Phase 2: Analysis Features
- [ ] Smart file grouping and filtering
- [ ] Automated comparative analysis
- [ ] Statistical analysis tools
- [ ] Enhanced visualization options

### Phase 3: Advanced Features
- [ ] Metadata database integration
- [ ] Batch processing capabilities
- [ ] Configuration file support
- [ ] Export and reporting tools

## File Structure
```
XDL Processing/
├── README.md                 # This file
├── adc_plot.py              # ADC analysis script
├── map_plot.py              # Map visualization script
├── data/                    # Data directory
│   ├── *.fits              # FITS image files
│   ├── *.map               # Detector map files
│   ├── *.phd               # Pulse height distributions
│   ├── adc_plot.py         # Duplicate script (to be removed)
│   └── map_plot.py         # Duplicate script (to be removed)
└── [future directories]
    ├── src/                # Source code modules
    ├── tests/              # Unit tests
    ├── config/             # Configuration files
    └── results/            # Analysis outputs
```

## Contributing

This project follows scientific software development best practices:
- Modular code design with clear separation of concerns
- Comprehensive error handling and logging
- Unit tests for critical functionality
- Documentation for all public interfaces
- Version control with meaningful commit messages

## License

[To be determined based on institutional requirements]

## Contact

[Contact information to be added]
