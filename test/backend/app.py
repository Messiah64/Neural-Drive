from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.decomposition import FastICA
from pycaret.classification import setup, compare_models, finalize_model, save_model, load_model, predict_model
import serial
import time
import threading
import queue
import os
import subprocess
from pathlib import Path
import sys
import glob
import asyncio
import websockets

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

# Global variables
recording_thread = None
inference_thread = None
data_queue = queue.Queue()
stop_event = threading.Event()
model = None
current_thread = None

# Add WebSocket globals
connected_clients = set()
loop = None

# Add WebSocket helper functions
async def _send_to_all(message: str):
    """Asynchronously send 'message' to all connected WebSocket clients."""
    if not connected_clients:
        return
    await asyncio.wait([ws.send(message) for ws in connected_clients])

def broadcast(message: str):
    """Thread-safe way to schedule an asynchronous broadcast."""
    if loop:
        asyncio.run_coroutine_threadsafe(_send_to_all(message), loop)

async def handle_client(websocket):
    """Handle WebSocket client connections."""
    print(f"Client connected: {websocket.remote_address}")
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"Received from client: {message}")
    except websockets.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    finally:
        connected_clients.remove(websocket)

async def start_websocket_server():
    """Start the WebSocket server."""
    print("Starting WebSocket server on ws://0.0.0.0:8080/")
    async with websockets.serve(handle_client, "0.0.0.0", 8080):
        await asyncio.Future()  # Run forever

def get_port():
    """Determine the appropriate port based on operating system"""
    if sys.platform.startswith('darwin'):  # macOS
        ports = glob.glob('/dev/cu.usbserial*') + glob.glob('/dev/tty.usbserial*')
        if ports:
            return ports[0]
        return '/dev/cu.usbmodem4827E2E5583C2'
    elif sys.platform.startswith('win'):   # Windows
        return 'COM10'
    else:  # Linux/Unix
        return '/dev/ttyUSB0'

def cleanup_port(port):
    """Attempt to clean up the serial port"""
    try:
        if sys.platform.startswith(('darwin', 'linux')):
            cmd = f"lsof {port}"
            try:
                output = subprocess.check_output(cmd.split()).decode()
                for line in output.split('\n')[1:]:
                    if line:
                        pid = line.split()[1]
                        print(f"Killing process {pid} using {port}")
                        os.system(f"kill -9 {pid}")
            except subprocess.CalledProcessError:
                pass
            
            if sys.platform.startswith('darwin'):
                os.system(f"stty -f {port} hupcl")
    except Exception as e:
        print(f"Cleanup warning: {e}")
    
    time.sleep(1)

def record_emg_data(port, duration, feature, data_queue, stop_event):
    try:
        print(f"Starting recording for feature: {feature}")
        cleanup_port(port)
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                ser = serial.Serial(
                    port=port,
                    baudrate=115200,
                    timeout=1,
                    rtscts=True,
                    dsrdtr=True
                )
                time.sleep(2)
                break
            except serial.SerialException as e:
                if attempt < max_attempts - 1:
                    print(f"Attempt {attempt + 1} failed. Retrying...")
                    cleanup_port(port)
                    time.sleep(2)
                else:
                    raise

        raw_data_1 = []
        raw_data_2 = []
        
        start_time = time.time()
        while (time.time() - start_time) < duration and not stop_event.is_set():
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line and ',' in line:
                    values = line.split(',')
                    if len(values) == 2:
                        raw_data_1.append(int(values[0]))
                        raw_data_2.append(int(values[1]))
            except (ValueError, UnicodeDecodeError) as e:
                continue

        ser.close()
        cleanup_port(port)

        if not raw_data_1 or not raw_data_2:
            raise Exception("No data was recorded!")

        # Process the recorded data
        raw_data_1 = np.array(raw_data_1).reshape(-1, 1)
        raw_data_2 = np.array(raw_data_2).reshape(-1, 1)
        combined_data = np.hstack((raw_data_1, raw_data_2))
        
        # Apply ICA
        ica = FastICA(n_components=2)
        independent_components = ica.fit_transform(combined_data)
        independent_components -= np.mean(independent_components, axis=0)
        
        # Create timestamps and DataFrame
        timestamps = np.linspace(0, duration, len(independent_components))
        df = pd.DataFrame({
            'Timestamp': timestamps,
            'Raw_EMG1': raw_data_1.flatten(),
            'Raw_EMG2': raw_data_2.flatten(),
            'IC1': independent_components[:, 0],
            'IC2': independent_components[:, 1],
            'Label': [feature] * len(independent_components)
        })
        
        # Save to CSV with feature name
        filename = f'data_{feature.lower()}.csv'
        df.to_csv(filename, index=False)
        print(f"Saved data for feature '{feature}' to {filename}")
        
        return True

    except Exception as e:
        print(f"Error in record_emg_data: {e}")
        data_queue.put({"status": "error", "message": str(e)})
        return False

def train_model_with_features():
    try:
        # Combine all feature data files
        all_data = []
        data_files = glob.glob('data_*.csv')
        
        if not data_files:
            raise Exception("No training data files found!")
            
        print(f"Found {len(data_files)} data files: {data_files}")
        
        for file in data_files:
            print(f"Reading file: {file}")
            df = pd.read_csv(file)
            print(f"Shape of data from {file}: {df.shape}")
            all_data.append(df)
        
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"Combined data shape: {combined_df.shape}")
        print(f"Unique labels: {combined_df['Label'].unique()}")
        
        # Setup pycaret with simplified parameters
        print("Setting up PyCaret...")
        exp = setup(
            data=combined_df,
            target='Label',
            verbose=False,
            fold=3,
            normalize=True,
            session_id=123,
            html=False,
            preprocess=True
        )
        
        # Train and save model
        print("Training model...")
        best_model = compare_models(n_select=1)
        print("Finalizing model...")
        final_model = finalize_model(best_model)
        print("Saving model...")
        save_model(final_model, 'nbest')
        
        print("Model training completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error in train_model_with_features: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def inference_loop(port, data_queue, stop_event):
    try:
        print("Loading model...")
        model = load_model('nbest')
        
        print(f"Connecting to port {port}...")
        ser = serial.Serial(
            port=port,
            baudrate=115200,
            timeout=1
        )
        time.sleep(2)
        
        print("Starting real-time predictions...")
        while not stop_event.is_set():
            raw_data_1 = []
            raw_data_2 = []
            
            start_time = time.time()
            while (time.time() - start_time) < 1.0:
                try:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line and ',' in line:
                        values = line.split(',')
                        if len(values) == 2:
                            raw_data_1.append(int(values[0]))
                            raw_data_2.append(int(values[1]))
                except (ValueError, UnicodeDecodeError):
                    continue

            if not raw_data_1 or not raw_data_2:
                continue

            # Process the data
            raw_data_1 = np.array(raw_data_1).reshape(-1, 1)
            raw_data_2 = np.array(raw_data_2).reshape(-1, 1)
            combined_data = np.hstack((raw_data_1, raw_data_2))
            
            # Apply ICA
            ica = FastICA(n_components=2)
            independent_components = ica.fit_transform(combined_data)
            independent_components -= np.mean(independent_components, axis=0)
            
            # Prepare for prediction
            timestamps = np.linspace(0, 1.0, len(independent_components))
            df_pred = pd.DataFrame({
                'Timestamp': timestamps,
                'Raw_EMG1': raw_data_1.flatten(),
                'Raw_EMG2': raw_data_2.flatten(),
                'IC1': independent_components[:, 0],
                'IC2': independent_components[:, 1]
            })
            
            # Make prediction
            predictions = predict_model(model, data=df_pred)
            pred_col = [col for col in predictions.columns if 'prediction' in col.lower()][0]
            prediction_counts = predictions[pred_col].value_counts()
            majority_prediction = prediction_counts.index[0]
            
            # Send prediction via WebSocket
            broadcast("1" if majority_prediction.upper() == "YES" else "0")
            
            # Update UI via data queue
            data_queue.put({
                "status": "prediction",
                "prediction": str(majority_prediction),
                "counts": {str(k): int(v) for k, v in prediction_counts.to_dict().items()},
                "samples": len(raw_data_1)
            })
            
        ser.close()
    except Exception as e:
        print(f"Inference error: {e}")
        data_queue.put({"status": "error", "message": str(e)})

@app.route('/api/record/start', methods=['POST'])
def start_recording():
    global current_thread, stop_event
    
    try:
        feature = request.json.get('feature')
        if not feature:
            return jsonify({"status": "error", "message": "Feature name is required"})
        
        if current_thread and current_thread.is_alive():
            return jsonify({"status": "error", "message": "Recording already in progress"})
        
        stop_event.clear()
        current_thread = threading.Thread(
            target=record_emg_data,
            args=(get_port(), 15, feature, data_queue, stop_event)
        )
        current_thread.start()
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/record/stop', methods=['POST'])
def stop_recording():
    global stop_event
    try:
        stop_event.set()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/train', methods=['POST'])
def train_model():
    try:
        success = train_model_with_features()
        if success:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Failed to train model"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/inference/start', methods=['POST'])
def start_inference():
    global current_thread, stop_event
    try:
        if current_thread and current_thread.is_alive():
            return jsonify({"status": "error", "message": "Inference already running"})
        
        stop_event.clear()
        current_thread = threading.Thread(
            target=inference_loop,
            args=(get_port(), data_queue, stop_event)
        )
        current_thread.start()
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/inference/stop', methods=['POST'])
def stop_inference():
    global stop_event
    try:
        stop_event.set()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/status')
def get_status():
    try:
        data = data_queue.get(timeout=0.1)
        return make_response(jsonify(data), 200)
    except queue.Empty:
        return make_response(jsonify({"status": "waiting"}), 200)
    except Exception as e:
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@app.route('/api/verify-data')
def verify_data():
    results = {}
    
    for motion in ['GO', 'STOP']:
        filename = f'n{motion.lower()}.csv'
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            results[motion] = {
                'exists': True,
                'samples': len(df),
                'size': os.path.getsize(filename)
            }
        else:
            results[motion] = {
                'exists': False,
                'samples': 0,
                'size': 0
            }
    return jsonify(results)

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return make_response(jsonify({
        "status": "error",
        "message": "Route not found"
    }), 404)

@app.errorhandler(500)
def server_error(e):
    return make_response(jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500)

@app.errorhandler(Exception)
def handle_exception(e):
    return make_response(jsonify({
        "status": "error",
        "message": str(e)
    }), 500)

if __name__ == '__main__':
    # Create the global event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start the WebSocket server
    websocket_task = loop.create_task(start_websocket_server())

    # Start Flask app in a separate thread
    from threading import Thread
    flask_thread = Thread(target=lambda: app.run(port=5000))
    flask_thread.daemon = True
    flask_thread.start()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        loop.close()