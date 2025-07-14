# Focused 5keV Integrated Plot Summary

## 🎯 **Plot Specifications Met**

Created a specialized focused plot for the 5keV integrated map with all requested specifications:

### ✅ **Technical Requirements**
- **Axis Limits**: X(200-900) and Y(200-900) pixels ✅
- **Aspect Ratio**: 1:1 (equal aspect) ✅
- **Title**: Shows beam energy (5 keV) and peak rate (137.3 counts/s) ✅
- **Azimuth Annotation**: "Azimuth walked around during data collection" ✅
- **File Formats**: PNG (raster) and SVG (scalar/vector) ✅

### 📊 **Plot Details**

**Data Characteristics**:
- **Beam Energy**: 5000 eV (5 keV)
- **Peak Rate**: 137.3 counts/s
- **Files Integrated**: 16 map files
- **Total Collection Time**: 87.0 seconds
- **Active Pixels in Crop**: 62,137 (out of 700×700 = 490,000)

**Visual Features**:
- **Colormap**: 'Hot' colormap for enhanced visibility
- **Scale**: Logarithmic (0.010 - 2.6 counts/s in cropped region)
- **Contours**: 5 percentile-based contour lines (50th, 75th, 90th, 95th, 99th)
- **Grid**: Semi-transparent grid for better readability
- **Annotation**: Positioned in upper-left corner with white background

## 📁 **Generated Files**

### **Primary Outputs**
1. **`results/5keV_focused_integrated_map.png`** - High-resolution raster (300 DPI)
2. **`results/5keV_focused_integrated_map.svg`** - Vector/scalar format
3. **`results/5keV_focused_integrated_map.pdf`** - Additional vector format

### **File Characteristics**
- **PNG**: 300 DPI resolution, white background, tight bounding box
- **SVG**: Scalable vector graphics, perfect for publications
- **PDF**: Vector format, suitable for documents and presentations

## 🔬 **Scientific Content**

### **Data Integration**
- **16 5keV map files** successfully integrated
- **Rate normalization** applied to account for varying collection times
- **Log scale visualization** reveals impact patterns across 3+ decades
- **Cropped region** focuses on the active detector area (200-900 pixels)

### **Impact Pattern Analysis**
- **62,137 active pixels** in the cropped region (12.7% coverage)
- **Clear impact regions** visible with distinct intensity patterns
- **Azimuth variation** captured across the integrated measurements
- **Peak intensity**: 2.6 counts/s in the cropped region

### **Experimental Context**
- **Azimuth walked around**: Annotation indicates systematic angular variation
- **5keV beam energy**: Higher energy than 1keV baseline measurements
- **ESA voltage**: 912V (optimized for 5keV operation)
- **Multiple measurements**: 16 files provide statistical robustness

## 🎯 **Key Features**

### **Enhanced Visibility**
- **Log scale**: Compresses wide dynamic range for better visibility
- **Hot colormap**: High contrast for impact region detection
- **White contours**: Clear delineation of intensity levels
- **Focused crop**: Eliminates empty detector regions

### **Professional Presentation**
- **Clean layout**: Minimal clutter, focused on data
- **Clear labeling**: Bold fonts, descriptive titles
- **Multiple formats**: Suitable for various publication needs
- **High quality**: 300 DPI PNG, scalable vector formats

### **Scientific Accuracy**
- **Proper scaling**: Maintains pixel-to-pixel correspondence
- **Rate normalization**: Accounts for varying measurement durations
- **Statistical integration**: Combines multiple measurements appropriately
- **Quality filtering**: Only valid measurements included

## 🚀 **Usage Commands**

### **Generate Focused Plot**
```bash
python create_5kev_focused_plot.py
```

### **Output Location**
```
results/
├── 5keV_focused_integrated_map.png  # High-res raster
├── 5keV_focused_integrated_map.svg  # Vector/scalar
└── 5keV_focused_integrated_map.pdf  # Vector PDF
```

## 📋 **Plot Specifications Summary**

| Specification | Value | Status |
|---------------|-------|--------|
| **X-axis limits** | 200-900 pixels | ✅ Met |
| **Y-axis limits** | 200-900 pixels | ✅ Met |
| **Aspect ratio** | 1:1 | ✅ Met |
| **Title content** | Beam energy + peak rate | ✅ Met |
| **Azimuth annotation** | Included | ✅ Met |
| **PNG format** | High-resolution | ✅ Met |
| **Scalar format** | SVG vector | ✅ Met |
| **Additional format** | PDF vector | ✅ Bonus |

## 🔍 **Technical Details**

### **Data Processing**
- **Original map size**: 1024×1024 pixels
- **Cropped region**: 700×700 pixels (200-900 range)
- **Log scale range**: 0.010 - 2.6 counts/s (in cropped region)
- **Contour levels**: Percentile-based for statistical relevance

### **Visualization Parameters**
- **Figure size**: 8×8 inches (1:1 aspect ratio)
- **DPI**: 300 for PNG output
- **Colormap**: 'hot' (black→red→yellow→white)
- **Contour colors**: White with 80% opacity
- **Grid**: Dashed lines with 30% opacity

### **File Optimization**
- **Tight bounding box**: Minimal whitespace
- **White background**: Clean, publication-ready
- **Vector formats**: Infinitely scalable
- **High DPI raster**: Suitable for high-quality printing

The focused 5keV plot successfully meets all specifications and provides a clear, professional visualization of the integrated detector response with proper azimuth annotation and multiple output formats!
