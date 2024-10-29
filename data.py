import serial
import pandas as pd
import numpy as np
from sklearn.decomposition import FastICA
import time

# Function to record EMG data
def record_emg_data(port, duration, label, sample_rate=1000):
    # Open serial connection
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)  # Wait for the connection to establish

    print(f"Recording {label} data for {duration} seconds...")
    start_time = time.time()
    raw_data = []

    while (time.time() - start_time) < duration:
        try:
            # Read data from the serial port
            line = ser.readline()
            line = line.decode('utf-8', errors='ignore').strip()
            if line:  # Ensure line is not empty
                # Append the raw EMG value
                raw_data.append(int(line))
        except Exception as e:
            print(f"Error reading data: {e}")

    # Close the serial connection
    ser.close()
    print(f"Finished recording {label} data.")

    # Convert to numpy array for ICA
    raw_data = np.array(raw_data).reshape(-1, 1)

    # Apply ICA
    ica = FastICA(n_components=1)
    independent_components = ica.fit_transform(raw_data)

    # Center the independent component around zero
    independent_components -= np.mean(independent_components)

    # Prepare the output with timestamps
    timestamps = np.linspace(0, duration, len(independent_components))
    return list(zip(timestamps, raw_data.flatten(), independent_components.flatten(), [label] * len(independent_components)))

# Main function to collect data  
def main():
    port = 'COM10'  # Update this with your Arduino's COM port
    duration = 15    # Duration to record for each label in seconds

    # Run code 2 times, to populate YES.csv and NO.csv independantly, then later  combine them with combine.py into data.csv



    
    # Collect YES data
    yes_data = record_emg_data(port, duration, 'YES')
    df = pd.DataFrame(yes_data, columns=['Timestamp', 'Raw_EMG', 'Independent_Component', 'Label'])
    df.to_csv('jyes.csv', index=False)
    '''
    
    # Collect NO data
    no_data = record_emg_data(port, duration, 'NO')
    df = pd.DataFrame(no_data, columns=['Timestamp', 'Raw_EMG', 'Independent_Component', 'Label'])
    df.to_csv('jno.csv', index=False)
    '''
   
    



if __name__ == "__main__":
    main()
