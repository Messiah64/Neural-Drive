import serial
import pandas as pd
import numpy as np
from sklearn.decomposition import FastICA
from pycaret.classification import load_model
import time

# Load the saved model
model = load_model('jbest')

# Function to read EMG data and make predictions
def predict_emg(port, sample_rate=1000):
    # Open serial connection
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)  # Wait for the connection to establish

    print("Starting real-time EMG predictions...")
    try:
        while True:
            raw_data = []
            # Read raw EMG data
            for _ in range(sample_rate):  # Collect data for 1 second
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    raw_data.append(int(line))

            # Prepare the data for prediction
            raw_data = np.array(raw_data).reshape(-1, 1)

            # Apply ICA (same setup as during training)
            ica = FastICA(n_components=1)
            independent_components = ica.fit_transform(raw_data)
            independent_components -= np.mean(independent_components)  # Center around zero

            # Create a DataFrame for prediction
            timestamps = np.linspace(0, sample_rate / 1000, len(independent_components))  # Create timestamps
            df_pred = pd.DataFrame({
                'Timestamp': timestamps,
                'Raw_EMG': raw_data.flatten(),
                'Independent_Component': independent_components.flatten(),
                'Label': [''] * len(independent_components)  # Placeholder for Label
            })

            # Predict using the loaded model
            predictions = model.predict(df_pred[['Timestamp', 'Raw_EMG', 'Independent_Component']])
            # print(f"Predictions: {predictions.values}")

            # Count occurrences of "YES" and "NO" in the predictions
            yes_count = (predictions == "YES").sum()
            no_count = (predictions == "NO").sum()

            # Check which count is higher and print the result
            if yes_count > no_count:
                print("YES")
            else:
                print("NO")

            print(type(predictions))
            print(predictions.shape)

    except KeyboardInterrupt:
        print("Stopping real-time predictions.")
    finally:
        ser.close()

# Call the prediction function
if __name__ == "__main__":
    predict_emg('COM10')  # Update with your Arduino's COM port
