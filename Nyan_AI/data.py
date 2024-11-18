import serial
import pandas as pd
import numpy as np
from sklearn.decomposition import FastICA
import time
import sys
import os
import glob
import subprocess

def cleanup_port(port):
    """Attempt to clean up the serial port"""
    try:
        # For Mac/Linux systems, try to kill processes using the port
        if sys.platform.startswith(('darwin', 'linux')):
            # Find processes using the port
            cmd = f"lsof {port}"
            try:
                output = subprocess.check_output(cmd.split()).decode()
                for line in output.split('\n')[1:]:  # Skip header
                    if line:
                        pid = line.split()[1]
                        print(f"Killing process {pid} using {port}")
                        os.system(f"kill -9 {pid}")
            except subprocess.CalledProcessError:
                pass  # No processes found
            
            # Additional cleanup for Mac
            if sys.platform.startswith('darwin'):
                os.system(f"stty -f {port} hupcl")  # Reset port settings
    except Exception as e:
        print(f"Cleanup warning: {e}")
    
    time.sleep(1)  # Wait for cleanup to take effect

def get_port():
    """Determine the appropriate port based on operating system"""
    if sys.platform.startswith('darwin'):  # macOS
        ports = glob.glob('/dev/cu.usbmodem*') + glob.glob('/dev/tty.usbmodem*')
        if ports:
            return ports[0]  # Return the first available port
        return '/dev/cu.usbmodem11201'
    elif sys.platform.startswith('win'):   # Windows
        return 'COM10'
    else:  # Linux/Unix
        return '/dev/ttyUSB0'

def record_emg_data(port, duration, label, sample_rate=1000):
    # Try to cleanup port first
    cleanup_port(port)
    
    # Try to open the serial connection with multiple attempts
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            ser = serial.Serial(
                port=port,
                baudrate=9600,
                timeout=1,
                rtscts=True,  # Enable hardware flow control
                dsrdtr=True   # Enable DSR/DTR flow control
            )
            time.sleep(2)  # Wait for the connection to establish
            break
        except serial.SerialException as e:
            if attempt < max_attempts - 1:
                print(f"Attempt {attempt + 1} failed. Retrying...")
                cleanup_port(port)
                time.sleep(2)
            else:
                print(f"Error opening port {port} after {max_attempts} attempts: {e}")
                print("\nTroubleshooting steps:")
                print("1. Run these commands in terminal:")
                print(f"   sudo chmod 666 {port}")
                print(f"   sudo chown $(whoami):staff {port}")
                print("2. Unplug and replug your device")
                print("3. Check if Arduino IDE or any other serial monitor is open")
                print(f"4. Current port is {port}, verify this is correct")
                return None

    print(f"Recording {label} data for {duration} seconds...")
    start_time = time.time()
    raw_data = []
    
    try:
        while (time.time() - start_time) < duration:
            try:
                # Read data from the serial port
                line = ser.readline()
                line = line.decode('utf-8', errors='ignore').strip()
                if line:
                    # Append the raw EMG value
                    raw_data.append(int(line))
            except (ValueError, UnicodeDecodeError) as e:
                print(f"Error reading data point: {e}")
                continue
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    finally:
        # Always close the serial connection
        ser.close()
        cleanup_port(port)  # Cleanup after we're done

    if not raw_data:
        print("No data was recorded!")
        return None

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
    return list(zip(timestamps, raw_data.flatten(), independent_components.flatten(), 
                   [label] * len(independent_components)))

def main():
    # Get the appropriate port for the current operating system
    port = get_port()
    print(f"Using port: {port}")
    duration = 15  # Duration to record for each label in seconds
    
    try:
        # Collect YES data
        # yes_data = record_emg_data(port, duration, 'GO')
        # if yes_data:
        #     df = pd.DataFrame(yes_data, 
        #                     columns=['Timestamp', 'Raw_EMG', 'Independent_Component', 'Label'])
        #     df.to_csv('nyes.csv', index=False)
        #     print("Successfully saved YES data to ngo.csv")
        
        # Uncomment to collect NO data
        no_data = record_emg_data(port, duration, 'STOP')
        if no_data:
            df = pd.DataFrame(no_data, 
                             columns=['Timestamp', 'Raw_EMG', 'Independent_Component', 'Label'])
            df.to_csv('nno.csv', index=False)
            print("Successfully saved NO data to nstop.csv")
            
    except Exception as e:
        print(f"An error occurred during data collection: {e}")

if __name__ == "__main__":
    main()