import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from tkinter import Tk, filedialog
import os
import numpy as np
matplotlib.use('Qt5Agg') 

def main():
    # Suppress the root Tkinter window
    Tk().withdraw()
    
    # Open file dialog to select multiple files
    file_paths = filedialog.askopenfilenames(
        title="Select Data Files",
        filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not file_paths:
        print("No files selected. Exiting.")
        return
    
    # Initialize plot
    plt.figure(figsize=(10, 6))
    
    for file_path in file_paths:
        # Read file into a DataFrame
        try:
            data = pd.read_csv(file_path, sep=r'\s+', header=None, names=["ADC Bin", "Count"])
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            continue
        
        # Filter bins within the range 11–245
        filtered_region = data[(data["ADC Bin"] > 10) & (data["ADC Bin"] <= 245)]
        if filtered_region.empty:
            print(f"No bins in the range 11–245 found in file '{os.path.basename(file_path)}'. Skipping.")
            continue

        data[(data["ADC Bin"] > 245)] = np.nan
        data[(data["ADC Bin"] < 2)] = np.nan
        
        # Calculate the area under the curve in the range 11–245
        area = np.trapz(filtered_region["Count"], filtered_region["ADC Bin"])
        if area == 0:
            print(f"Area under the curve is zero for file '{os.path.basename(file_path)}'. Skipping.")
            continue
        
        # Normalize the counts so the area under the curve is 1
        data["Normalized Count"] = data["Count"] / area
        
        # Prompt user for a legend label for the file
        label = input(f"Enter a label for the file '{os.path.basename(file_path)}': ")
        
        # Plot the normalized histogram
        plt.plot(data["ADC Bin"], data["Normalized Count"], label=label)
    
    # Customize the plot
    plt.title("Normalized ADC Bin Counts (Area Under Curve = 1)", fontsize=16)
    plt.xlabel("ADC Bin", fontsize=14)
    plt.ylabel("Normalized Count", fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True)
    
    # Show the plot
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
