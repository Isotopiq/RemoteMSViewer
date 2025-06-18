# ThermoAPI Remote Server

This is a remote server implementation for the ThermoAPI mass spectrometry data. It receives data from the ThermoAPI backend and provides APIs to access the data.

## Features

- Receives mass spectrometry data from ThermoAPI backend
- Stores data in memory with configurable limits
- Provides REST API endpoints to access the data
- Supports real-time data streaming via Socket.IO and Server-Sent Events (SSE)
- Optional API key authentication

## Setup

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. Clone this repository or navigate to the remote_server directory
2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Linux/Mac
pip install -r requirements.txt