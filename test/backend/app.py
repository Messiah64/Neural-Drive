from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.decomposition import FastICA
import serial
import time
import threading
import queue
import os
import subprocess
from pathlib import Path

app = Flask(__name__)
# Update CORS configuration to be more permissive during development
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
    }
})

# Global variables
recording_thread = None
inference_thread = None
data_queue = queue.Queue()
stop_recording = threading.Event()
model = None

def record_emg_data(port, duration, label, data_queue, stop_event):
    try:
        ser = serial.Serial(port=port, baudrate=9600, timeout=1)
        time.sleep(2)
        
        start_time = time.time()
        raw_data = []
        
        while (time.time() - start_time) < duration and not stop_event.is_set():
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    raw_data.append(int(line))
            except (ValueError, UnicodeDecodeError) as e:
                continue
                
        ser.close()
        
        if raw_data:
            # Process the data
            raw_data = np.array(raw_data).reshape(-1, 1)
            ica = FastICA(n_components=1)
            independent_components = ica.fit_transform(raw_data)
            independent_components -= np.mean(independent_components)
            
            # Create DataFrame
            timestamps = np.linspace(0, duration, len(independent_components))
            data = list(zip(timestamps, raw_data.flatten(), independent_components.flatten(), 
                          [label] * len(independent_components)))
            
            df = pd.DataFrame(data, columns=['Timestamp', 'Raw_EMG', 'Independent_Component', 'Label'])
            df.to_csv(f'n{label.lower()}.csv', index=False)
            
            data_queue.put({"status": "success", "message": f"Recorded {label} data"})
        else:
            data_queue.put({"status": "error", "message": "No data recorded"})
            
    except Exception as e:
        data_queue.put({"status": "error", "message": str(e)})

def train_model():
    try:
        # Check if all required files exist
        required_files = [f'n{motion.lower()}.csv' for motion in ['GO', 'STOP']]
        missing_files = [f for f in required_files if not Path(f).exists()]
        
        if missing_files:
            return {"status": "error", "message": f"Missing data files: {', '.join(missing_files)}"}

        # Combine the data files
        dfs = []
        for file in required_files:
            df = pd.read_csv(file)
            dfs.append(df)
        
        combined_df = pd.concat(dfs, ignore_index=True)
        combined_df.to_csv('ndata.csv', index=False)

        # Run the model training notebook
        result = subprocess.run(['jupyter', 'nbconvert', '--execute', '--to', 'notebook', 
                               '--ExecutePreprocessor.timeout=600', 'model.ipynb'],
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            return {"status": "error", "message": f"Model training failed: {result.stderr}"}
        
        # Check if model file was created
        if not Path('nbest.pkl').exists():
            return {"status": "error", "message": "Model file was not created"}
        
        return {"status": "success", "message": "Model trained successfully"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

def inference_loop(port, data_queue, stop_event):
    try:
        from pycaret.classification import load_model
        model = load_model('nbest')
        
        ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(2)
        
        while not stop_event.is_set():
            raw_data = []
            for _ in range(1000):  # 1 second of data
                if stop_event.is_set():
                    break
                    
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    raw_data.append(int(line))
                    
            if raw_data:
                # Process data
                raw_data = np.array(raw_data).reshape(-1, 1)
                ica = FastICA(n_components=1)
                independent_components = ica.fit_transform(raw_data)
                independent_components -= np.mean(independent_components)
                
                # Prepare for prediction
                timestamps = np.linspace(0, 1, len(independent_components))
                df_pred = pd.DataFrame({
                    'Timestamp': timestamps,
                    'Raw_EMG': raw_data.flatten(),
                    'Independent_Component': independent_components.flatten(),
                    'Label': [''] * len(independent_components)
                })
                
                # Make prediction
                predictions = model.predict(df_pred[['Timestamp', 'Raw_EMG', 'Independent_Component']])
                
                # Count predictions for each motion
                prediction_counts = pd.Series(predictions).value_counts()
                prediction = prediction_counts.index[0]  # Get the most common prediction
                
                data_queue.put({"status": "prediction", "prediction": prediction})
                
        ser.close()
    except Exception as e:
        data_queue.put({"status": "error", "message": str(e)})

@app.route('/api/record', methods=['POST'])
def start_recording():
    global recording_thread, stop_recording
    
    if recording_thread and recording_thread.is_alive():
        return jsonify({"status": "error", "message": "Recording already in progress"})
    
    motion = request.json.get('motion')
    if not motion:
        return jsonify({"status": "error", "message": "Motion type required"})
    
    if motion not in ['GO', 'STOP']:
        return jsonify({"status": "error", "message": "Invalid motion type. Must be GO or STOP"})
    
    stop_recording.clear()
    recording_thread = threading.Thread(
        target=record_emg_data,
        args=('/dev/cu.usbmodem11401', 15, motion, data_queue, stop_recording)
    )
    recording_thread.start()
    
    return jsonify({"status": "success", "message": "Recording started"})

@app.route('/api/stop-recording', methods=['POST'])
def stop_recording_endpoint():
    global stop_recording
    
    if recording_thread and recording_thread.is_alive():
        stop_recording.set()
        recording_thread.join()
        return jsonify({"status": "success", "message": "Recording stopped"})
    
    return jsonify({"status": "error", "message": "No recording in progress"})

@app.route('/api/train', methods=['POST'])
def train_endpoint():
    result = train_model()
    return jsonify(result)

@app.route('/api/start-inference', methods=['POST'])
def start_inference():
    global inference_thread, stop_recording
    
    # Check if model exists
    if not Path('nbest.pkl').exists():
        return jsonify({"status": "error", "message": "Model not trained yet. Please train the model first."})
    
    if inference_thread and inference_thread.is_alive():
        return jsonify({"status": "error", "message": "Inference already running"})
    
    stop_recording.clear()
    inference_thread = threading.Thread(
        target=inference_loop,
        args=('/dev/cu.usbmodem11401', data_queue, stop_recording)
    )
    inference_thread.start()
    
    return jsonify({"status": "success", "message": "Inference started"})

@app.route('/api/stop-inference', methods=['POST'])
def stop_inference():
    global stop_recording, inference_thread
    
    if inference_thread and inference_thread.is_alive():
        stop_recording.set()
        inference_thread.join()
        return jsonify({"status": "success", "message": "Inference stopped"})
    
    return jsonify({"status": "error", "message": "No inference running"})

@app.route('/api/status')
def get_status():
    try:
        data = data_queue.get_nowait()
        return jsonify(data)
    except queue.Empty:
        return jsonify({"status": "waiting"})

if __name__ == '__main__':
    app.run(port=5000)