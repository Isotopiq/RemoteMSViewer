# Mass Spec Real-time Viewer

A web-based application for real-time visualization of mass spectrometry data using Thermo Fisher's Instrument API (IAPI).

## Features

- Real-time display of mass spectrometry data
- Interactive plots using Plotly
- Display of centroid and noise data
- Modern UI with Material-UI components
- WebSocket-based real-time updates

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- Thermo Fisher IAPI libraries
- A compatible mass spectrometer

## Project Structure

```
web_viewer/
├── backend/
│   ├── main.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   └── main.jsx
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## Setup

### Backend

1. Create a Python virtual environment:
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the backend server:
   ```bash
   python main.py
   ```

### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

## Usage

1. Ensure your mass spectrometer is connected and properly configured
2. Start the backend server
3. Start the frontend development server
4. Open your browser and navigate to `http://localhost:3000`
5. The application will automatically connect to the instrument and begin displaying real-time data

## Data Display

- The main plot shows both centroid data (as points) and noise data (as dotted lines)
- The latest scan information panel shows detailed information about the most recent scan
- The plot automatically updates as new scans arrive
- The y-axis uses a logarithmic scale for better visualization of intensity values

## Notes

- The application keeps the last 5 scans in the plot for visualization
- The WebSocket connection will automatically reconnect if disconnected
- Make sure the IAPI libraries are properly installed and accessible to the Python environment