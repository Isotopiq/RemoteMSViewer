import os
import json
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from flask_socketio import SocketIO
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("remote_server.log"),
        logging.StreamHandler()
    ]
)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Queue for Server-Sent Events (SSE)
scan_data_queue = queue.Queue(maxsize=100)

# In-memory storage for scan data
class DataStorage:
    def __init__(self):
        self.lock = threading.Lock()
        self.scan_data = {}
        self.latest_scan_number = 0
        self.max_scans_to_keep = 1000  # Adjust based on memory constraints
    
    def add_scan(self, scan_data):
        with self.lock:
            scan_number = scan_data.get('scan_number', 0)
            self.scan_data[scan_number] = scan_data
            self.latest_scan_number = max(self.latest_scan_number, scan_number)
            
            # Clean up old scans if we exceed the limit
            if len(self.scan_data) > self.max_scans_to_keep:
                # Remove oldest scans
                scan_numbers = sorted(self.scan_data.keys())
                for old_scan in scan_numbers[:len(scan_numbers) - self.max_scans_to_keep]:
                    del self.scan_data[old_scan]
    
    def get_latest_scan(self):
        with self.lock:
            if not self.scan_data:
                return None
            return self.scan_data.get(self.latest_scan_number)
    
    def get_scan(self, scan_number):
        with self.lock:
            return self.scan_data.get(scan_number)
    
    def get_scan_range(self, start_scan, end_scan):
        with self.lock:
            result = {}
            for scan_num in range(start_scan, end_scan + 1):
                if scan_num in self.scan_data:
                    result[scan_num] = self.scan_data[scan_num]
            return result

# Initialize data storage
data_storage = DataStorage()

# API key validation middleware
def validate_api_key():
    # Get API key from config
    api_key = os.environ.get('API_KEY')
    
    # If no API key is configured, skip validation
    if not api_key:
        return True
    
    # Get authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
    
    # Check if it's a Bearer token
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return False
    
    # Validate the token
    return parts[1] == api_key

# Routes
@app.route('/api/data', methods=['POST'])
def receive_data():
    # Validate API key if configured
    if not validate_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized",
            "timestamp": datetime.now().isoformat()
        }), 401
    
    try:
        # Get data from request
        scan_data = request.json
        
        # Validate data
        if not scan_data or not isinstance(scan_data, dict):
            return jsonify({
                "success": False,
                "error": "Invalid data format",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Add timestamp if not present
        if 'timestamp' not in scan_data:
            scan_data['timestamp'] = datetime.now().isoformat()
        
        # Store the data
        data_storage.add_scan(scan_data)
        
        # Emit via Socket.IO
        socketio.emit('scan_data', scan_data)
        
        # Add to SSE queue (non-blocking, drop if queue is full)
        try:
            scan_data_queue.put_nowait(scan_data)
        except queue.Full:
            # If queue is full, remove oldest item and add new one
            try:
                scan_data_queue.get_nowait()
                scan_data_queue.put_nowait(scan_data)
            except Exception:
                pass
        
        logging.info(f"Received scan #{scan_data.get('scan_number')} with {len(scan_data.get('masses', []))} data points")
        
        return jsonify({
            "success": True,
            "message": "Data received",
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logging.error(f"Error processing data: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/data/latest', methods=['GET'])
def get_latest_data():
    try:
        latest_scan = data_storage.get_latest_scan()
        
        if not latest_scan:
            return jsonify({
                "success": False,
                "error": "No data available",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        return jsonify({
            "success": True,
            "scan_data": latest_scan,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logging.error(f"Error getting latest data: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/data/<int:scan_number>', methods=['GET'])
def get_scan_data(scan_number):
    try:
        scan_data = data_storage.get_scan(scan_number)
        
        if not scan_data:
            return jsonify({
                "success": False,
                "error": f"Scan #{scan_number} not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        return jsonify({
            "success": True,
            "scan_data": scan_data,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logging.error(f"Error getting scan data: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/data/range', methods=['GET'])
def get_scan_range():
    try:
        start_scan = request.args.get('start', type=int)
        end_scan = request.args.get('end', type=int)
        
        if start_scan is None or end_scan is None:
            return jsonify({
                "success": False,
                "error": "Missing start or end parameters",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        if start_scan > end_scan:
            return jsonify({
                "success": False,
                "error": "Start scan must be less than or equal to end scan",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        scan_data = data_storage.get_scan_range(start_scan, end_scan)
        
        if not scan_data:
            return jsonify({
                "success": False,
                "error": "No scans found in specified range",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        return jsonify({
            "success": True,
            "scan_data": scan_data,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logging.error(f"Error getting scan range: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/events')
def events():
    def event_stream():
        while True:
            try:
                # Get data from queue with a timeout to allow for clean shutdown
                data = scan_data_queue.get(timeout=1)
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                # Send a keep-alive comment to prevent connection timeout
                yield ": keep-alive\n\n"
            except Exception as e:
                logging.error(f"Error in event stream: {e}")
                break
    
    return Response(stream_with_context(event_stream()),
                  mimetype="text/event-stream",
                  headers={"Cache-Control": "no-cache",
                           "Connection": "keep-alive",
                           "Access-Control-Allow-Origin": "*"})

@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        latest_scan = data_storage.get_latest_scan()
        scan_count = len(data_storage.scan_data)
        
        return jsonify({
            "success": True,
            "status": {
                "server_running": True,
                "scan_count": scan_count,
                "latest_scan_number": data_storage.latest_scan_number,
                "latest_scan_timestamp": latest_scan.get('timestamp') if latest_scan else None,
                "timestamp": datetime.now().isoformat()
            }
        })
    
    except Exception as e:
        logging.error(f"Error getting status: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Serve static files
# Update the route to serve the index.html file
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join('static', path)):
        return app.send_static_file(path)
    elif os.path.exists(os.path.join('static', 'index.html')):
        return app.send_static_file('index.html')
    else:
        return jsonify({
            "status": "running",
            "message": "ThermoAPI Remote Server is running. Use the API endpoints to interact with the server.",
            "endpoints": {
                "/api/data": "POST - Send data to the server",
                "/api/data/latest": "GET - Get the latest scan data",
                "/api/data/<scan_number>": "GET - Get a specific scan by number",
                "/api/data/range": "GET - Get a range of scans",
                "/api/events": "GET - SSE endpoint for real-time data",
                "/api/status": "GET - Get server status"
            },
            "timestamp": datetime.now().isoformat()
        })

# Run the server
if __name__ == '__main__':
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Create static folder if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    # Get port from environment variable with fallback to 5001
    port = int(os.environ.get('PORT', 5001))
    
    # Log startup information
    logging.info(f"Starting remote server on port {port}")
    logging.info(f"API Key authentication: {'Enabled' if os.environ.get('API_KEY') else 'Disabled'}")
    
    # Run the server
    socketio.run(app, host='0.0.0.0', port=port, debug=False)