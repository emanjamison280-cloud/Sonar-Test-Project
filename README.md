# Sonar Test Project

A Python-based sonar wave detection system using webcam input. This project focuses on creating a functional sonar detection prototype that can be later integrated with YOLOv8 object detection and LiDAR.

## Project Overview

- **Stage 1 (Current)**: Sonar wave detection and visualization using webcam
- **Stage 2**: YOLOv8 object detection integration
- **Stage 3**: LiDAR integration
- **Stage 4**: Wave overlay visualization

## Features

- Real-time webcam capture
- Sonar wave simulation and visualization
- Distance estimation (6-foot range)
- Radar-style wave visualization
- Modular architecture for easy integration

## Requirements

- Python 3.8+
- OpenCV
- NumPy
- Matplotlib

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python src/main.py
```

## Project Structure

```
Sonar-Test-Project/
├── src/
│   ├── sonar_detector.py      # Sonar detection and wave processing
│   ├── camera_handler.py       # Webcam capture and preprocessing
│   ├── wave_visualizer.py      # Radar-style visualization
│   └── main.py                 # Application entry point
├── config/
│   └── config.py               # Configuration settings
├── requirements.txt
└── README.md
```

## Controls

- **q** - Quit application
- **SPACE** - Force wave trigger at current distance

## How It Works

1. **Camera Input**: Captures real-time video from your webcam
2. **Sonar Detection**: Analyzes frames using edge detection and motion analysis to estimate distance
3. **Wave Visualization**: Displays sonar waves in a radar-style interface
4. **Distance Estimation**: Tracks objects up to 6 feet away

## Next Steps

1. Test sonar wave detection with webcam
2. Optimize distance estimation
3. Integrate YOLOv8 for object detection
4. Add LiDAR support
5. Create overlay visualization
