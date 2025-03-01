# Neural Control System

A brain-computer interface (BCI) system that enables control of physical devices through neural signal processing and classification.

## Overview

This project implements a complete neural control system with the following components:

1. **Web Interface** - A React-based UI for feature calibration and real-time monitoring
2. **Backend Server** - A Flask Python application that processes EMG/neural signals, trains ML models, and communicates predictions
3. **IoT Devices** - ESP32-based devices that receive commands and control physical components:
   - **House Device** - Controls a servo and NeoPixel display
   - **Car Device** - Controls motors with directional LED indicators

The system captures neural or EMG signals, processes them using Independent Component Analysis (ICA), classifies them with machine learning, and sends binary control signals (0/1) to connected devices via WebSockets.

## Components

### Web Interface (`page.tsx`)

A React-based user interface that provides:

- Feature management (add/remove control features)
- Recording calibration data for each feature
- Training the classification model
- Real-time prediction monitoring
- Visual feedback on system status

![Web Interface Screenshot](https://placeholder-img.com/web-interface.jpg)

### Backend Server (`app.py`)

A Flask-based server that:

- Captures EMG/neural signals via serial connection
- Processes signals using Fast ICA
- Trains classification models using PyCaret
- Provides REST API endpoints for feature management, recording, training, and prediction
- Broadcasts binary control signals via WebSocket

### IoT Device: House Controller (`2ch_house.ino`)

ESP32-based device that:

- Connects to WiFi and WebSocket server
- Controls a continuous rotation servo (360°)
- Drives a NeoPixel 8x8 LED matrix for visual feedback
- Responds to binary commands (0/1):
  - `1`: Activates servo rotation and rapid color cycling
  - `0`: Stops servo and turns off LEDs

### IoT Device: Car Controller (`2ch_car.ino`)

ESP32-based device that:

- Connects to WiFi and WebSocket server
- Controls two DC motors for vehicle movement
- Drives a NeoPixel 8x8 LED matrix for visual indicators
- Responds to binary commands (0/1):
  - `1`: Activates forward motion with animated green arrows
  - `0`: Stops motors and displays a red stop sign

## Setup Instructions

### Prerequisites

- Python 3.7+
- Node.js and npm
- ESP32 microcontrollers
- USB-compatible EMG/neural signal device
- Arduino IDE with ESP32 support

### Backend Setup

1. Install Python dependencies:
   ```bash
   pip install flask flask-cors pandas numpy scikit-learn pycaret serial websockets

2. Connect your EMG/neural signal device to your computer via USB
3. Run the Flask server:
   ```bash
   python app.py
   ```
### Frontend Setup

1. Install Node.js dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

Access the web interface at `http://localhost:3000`

### IoT Device Setup

1. Open the Arduino IDE and install the following libraries:
   - WiFi
   - ArduinoWebsockets
   - ESP32Servo
   - Adafruit_NeoPixel

2. For each device (house and car):
   - Open the corresponding .ino file
   - Update WiFi credentials (SSID and PASSWORD)
   - Update WebSocket server details (WS_HOST and WS_PORT)
   - Verify and upload the code to the ESP32 device
   - Monitor the serial output to confirm successful connections

### Usage Guide

#### Calibration and Training

1. Add Features: Enter feature names (e.g., "Left", "Right") and click "Add Feature"
2. Record Calibration Data:
   - For each feature, click its button to start a 15-second recording session
   - Think about or perform the action associated with that feature
   - Data is automatically saved when the timer completes

3. Train Model: Once all features are calibrated, click "Train Model"

#### Start Processing

1. Click "Start Real-time Processing" to begin classification

#### Device Control

Once calibrated and trained:

The system will continuously classify your neural/EMG signals   
When a signal is classified as feature 1, connected devices will activate:

- House controller: servo will spin and LEDs will cycle colors
- Car controller: motors will move forward and LEDs will show green arrows


When a signal is classified as feature 0, devices will deactivate:

- House controller: servo will stop and LEDs will turn off
- Car controller: motors will stop and LEDs will show a red stop sign



