import matplotlib.pyplot as plt
import numpy as np
from tkinter import Tk, filedialog

def find_end_of_header(content):
    """
    Finds the position of the 'END' keyword in the header content.
    """
    try:
        header_end_index = content.index(b'END') + 3  # Find 'END' and skip its length
        # Align to the next 2880-byte block as per FITS standard
        header_end_index = ((header_end_index + 2879) // 2880) * 2880
        return header_end_index
    except ValueError:
        return None

def process_full_file(file_path):
    """
    Process the full file to locate the header end and extract binary image data.
    """
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # Find the end of the header
    header_end_index = find_end_of_header(content)
    
    if header_end_index is not None:
        binary_data_start = header_end_index
        binary_data = content[binary_data_start:]
        return binary_data
    else:
        raise ValueError("Could not locate the 'END' keyword in the file.")

def main():
    # Suppress the root Tkinter window
    Tk().withdraw()
    
    # Open file dialog to select the map file
    file_path = filedialog.askopenfilename(
        title="Select Map File",
        filetypes=[("Map files", "*.map"), ("All files", "*.*")]
    )
    
    if not file_path:
        print("No file selected. Exiting.")
        return
    
    try:
        # Extract binary data from the full file
        full_binary_data = process_full_file(file_path)
        
        # Assume dimensions and data type
        width, height = 1024, 1024  # Adjust these dimensions if necessary
        dtype = np.int16  # Based on BITPIX = 16
        expected_size = width * height
        
        # Convert binary data into a numpy array
        image_data = np.frombuffer(full_binary_data, dtype=dtype)
        
        # Check and handle size mismatch
        if image_data.size > expected_size:
            print(f"Trimming excess data: {image_data.size - expected_size} elements")
            image_data = image_data[:expected_size]  # Trim excess data
        elif image_data.size < expected_size:
            raise ValueError("Binary data is smaller than expected dimensions.")
        
        # Reshape the array into the desired dimensions
        image_data = image_data.reshape((height, width))
        
        # Adjust colorbar range for better contrast
        vmin = np.percentile(image_data, 1)  # 1st percentile
        vmax = np.percentile(image_data, 95)  # 99th percentile
        
        # Plot the extracted image data
        plt.figure(figsize=(8, 6))
        img = plt.imshow(image_data, cmap='viridis', aspect='auto', vmin=vmin, vmax=vmax)
        plt.colorbar(img, label='Gain [Arbitrary Units]')
        plt.inferno()
        plt.title('LMS-1D Round #2 (UV Source)')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.show()
        
    except Exception as e:
        print(f"Error processing the file: {e}")

if __name__ == "__main__":
    main()
