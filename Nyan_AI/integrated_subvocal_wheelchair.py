import serial
import pandas as pd
import numpy as np
from sklearn.decomposition import FastICA
from pycaret.classification import load_model
import time
import asyncio
import websockets
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# WebSocket URI for ESP32
ESP32_URI = "ws://192.168.43.53:80"

# Global variables
last_function_call_time = time.time()
latest_prediction = "NO"
previous_prediction = "NO"  # Added to track previous state

# Load the saved model
model = load_model('best')

async def send_command_via_websocket(command):
    try:        
        async with websockets.connect(ESP32_URI) as websocket:
            await websocket.send(command)
            print(f"Sent command via WebSocket: {command}")
    except Exception as e:
        print(f"Failed to send command via WebSocket: {e}")

def MOVE():
    print("Function MOVE: Prediction is YES")
    asyncio.run(send_command_via_websocket('MOVE'))

def STAY():
    print("Function STAY: Prediction is NO")
    asyncio.run(send_command_via_websocket('STAY'))

@app.route('/get_prediction', methods=['GET'])
def get_prediction():
    return jsonify({"prediction": latest_prediction}), 200

def run_flask():
    app.run(debug=False, port=5000)

def predict_emg(port, sample_rate=1000):
    global latest_prediction, last_function_call_time, previous_prediction
    
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

            # Apply ICA
            ica = FastICA(n_components=1)
            independent_components = ica.fit_transform(raw_data)
            independent_components -= np.mean(independent_components)

            # Create DataFrame for prediction
            timestamps = np.linspace(0, sample_rate / 1000, len(independent_components))
            df_pred = pd.DataFrame({
                'Timestamp': timestamps,
                'Raw_EMG': raw_data.flatten(),
                'Independent_Component': independent_components.flatten(),
                'Label': [''] * len(independent_components)
            })

            # Make predictions
            predictions = model.predict(df_pred[['Timestamp', 'Raw_EMG', 'Independent_Component']])

            # Count occurrences of "YES" and "NO"
            yes_count = (predictions == "YES").sum()
            no_count = (predictions == "NO").sum()

            # Update latest prediction and send command
            current_time = time.time()
            if current_time - last_function_call_time >= 1:  # Rate limiting to 1 second
                current_prediction = "YES" if yes_count > no_count else "NO"
                
                # Only update and send command if:
                # 1. Current prediction is NO (always allow STAY commands)
                # 2. OR if previous prediction was NO (allow first MOVE after STAY)
                if current_prediction == "NO" or previous_prediction == "NO":
                    latest_prediction = current_prediction
                    if current_prediction == "YES":
                        MOVE()
                    else:
                        STAY()
                    previous_prediction = current_prediction
                    last_function_call_time = current_time

    except KeyboardInterrupt:
        print("Stopping real-time predictions.")
    finally:
        ser.close()

def main():
    # Start Flask in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start EMG prediction
    predict_emg('COM10')  # Update with your Arduino's COM port

if __name__ == "__main__":
    main()