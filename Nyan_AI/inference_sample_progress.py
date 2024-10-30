import pandas as pd
import numpy as np
from sklearn.decomposition import FastICA
# from pycaret.classification import load_model
import time
from tqdm import tqdm

# Simulate model predictions instead of loading real model
class SimulatedModel:
    def predict(self, X):
        # Randomly predict YES or NO with slight bias
        n_samples = len(X)
        return np.random.choice(['YES', 'NO'], size=n_samples, p=[0.6, 0.4])

# Create simulated model instance
model = SimulatedModel()

def simulate_emg(sample_rate=1000):
    print("Starting simulated EMG predictions...")
    try:
        while True:
            # Create progress bar for simulated data collection
            pbar = tqdm(total=sample_rate, desc="Collecting EMG data", 
                       bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} samples')
            
            # Simulate raw EMG data collection
            raw_data = []
            for _ in range(sample_rate):
                # Simulate EMG signal: random noise + sine wave
                t = _ / sample_rate
                signal = np.sin(2 * np.pi * 10 * t) + np.random.normal(0, 0.5)
                raw_data.append(signal)
                pbar.update(1)
                time.sleep(0.001)  # Small delay to simulate real-time collection
            
            pbar.close()

            # Processing indicator
            print("Processing data...", end='\r')

            # Prepare the simulated data
            raw_data = np.array(raw_data).reshape(-1, 1)

            # Apply ICA
            ica = FastICA(n_components=1)
            independent_components = ica.fit_transform(raw_data)
            independent_components -= np.mean(independent_components)

            # Create a DataFrame for prediction
            timestamps = np.linspace(0, sample_rate / 1000, len(independent_components))
            df_pred = pd.DataFrame({
                'Timestamp': timestamps,
                'Raw_EMG': raw_data.flatten(),
                'Independent_Component': independent_components.flatten(),
                'Label': [''] * len(independent_components)
            })

            # Get predictions from simulated model
            predictions = model.predict(df_pred[['Timestamp', 'Raw_EMG', 'Independent_Component']])

            # Count occurrences of "YES" and "NO"
            yes_count = (predictions == "YES").sum()
            no_count = (predictions == "NO").sum()

            # Clear the processing message
            print(" " * 50, end='\r')
            
            # Display the decision
            print(f"Decision: {'YES' if yes_count > no_count else 'NO'}\n")

    except KeyboardInterrupt:
        print("\nStopping simulated predictions.")

# Run the simulation
if __name__ == "__main__":
    simulate_emg()