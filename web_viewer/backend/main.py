import os
import sys
import time
import json
import signal
import logging
import clr
import atexit
import threading
import requests
import queue
from datetime import datetime
from flask import Flask, jsonify, Response, stream_with_context
from flask_socketio import SocketIO
from flask_cors import CORS
from threading import Lock

# Configure logging
# MODIFIED: Consolidated logging setup to include FileHandler for backend_debug.log
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend_debug.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='w'), # 'w' to overwrite on each run
        logging.StreamHandler(sys.stdout) # Keep console output
    ]
)

# ADDED: Initial diagnostic logging
logging.info(f"Backend script started. CWD: {os.getcwd()}")
logging.info(f"Python executable: {sys.executable}")
logging.info(f"sys.path: {sys.path}")

# Initialize .NET runtime and load assemblies
def initialize_dotnet(debug_mode=True):
    # Set up API path
    API_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib')
    sys.path.append(API_PATH)
    logging.info(f"API PATH: {API_PATH}")
    
    if debug_mode:
        logging.info("Current directory structure:")
        for root, dirs, files in os.walk(API_PATH):
            logging.info(f"\nDirectory: {root}")
            for d in dirs:
                logging.info(f"  Dir: {d}")
            for f in files:
                logging.info(f"  File: {f}")
    
    def verify_assembly_path(path):
        """Verify that the assembly file exists"""
        if not os.path.exists(path):
            logging.error(f"Assembly file not found: {path}")
            logging.error(f"Directory contents: {os.listdir(os.path.dirname(path))}")
            return False
        if debug_mode:
            logging.info(f"Verified assembly exists: {path}")
            logging.info(f"File size: {os.path.getsize(path)} bytes")
        return True
    try:
        import clr
        import pythonnet
        logging.info("Initializing .NET runtime...")
        
        # Ensure clean state
        try:
            pythonnet.load("coreclr")
            if debug_mode:
                logging.info("CoreCLR loaded successfully")
        except Exception as e:
            logging.warning(f"Initial runtime load attempt: {e}")
        
        # Load required assemblies with retry
        max_retries = 3
        retry_delay = 2
        exploris_path = os.path.join(API_PATH, 'Exploris4.3-and-higher')
        assemblies = [
            os.path.join(exploris_path, 'Thermo.API.NetStd-1.0.dll'),
            os.path.join(exploris_path, 'Thermo.API.Exploris.NetStd-1.0.dll'),
            os.path.join(exploris_path, 'Thermo.API.Spectrum.NetStd-1.0.dll')
        ]
        
        loaded_assemblies = []
        for assembly_path in assemblies:
            if not verify_assembly_path(assembly_path):
                raise FileNotFoundError(f"Assembly not found: {assembly_path}")
            
            assembly_name = os.path.basename(assembly_path)
            for attempt in range(max_retries):
                try:
                    if debug_mode:
                        logging.info(f"Attempt {attempt + 1} to load assembly: {assembly_name}")
                    clr.AddReference(assembly_path)
                    loaded_assemblies.append(assembly_name)
                    
                    if debug_mode:
                        try:
                            assembly = clr.GetClrType(assembly_name.replace('.dll', '')).Assembly
                            logging.info(f"Assembly {assembly_name} loaded successfully")
                            logging.info(f"Version: {assembly.GetName().Version}")
                        except Exception as e:
                            logging.warning(f"Could not get assembly details: {e}")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logging.error(f"Failed to load assembly {assembly_name} after {max_retries} attempts")
                        logging.error(f"Error details: {str(e)}")
                        logging.error(f"Loaded assemblies so far: {loaded_assemblies}")
                        raise
                    logging.warning(f"Attempt {attempt + 1} to load {assembly_name} failed: {e}")
                    import time
                    time.sleep(retry_delay)
        
        if debug_mode:
            logging.info("Loaded assemblies summary:")
            for assembly in loaded_assemblies:
                logging.info(f"  - {assembly}")
        
        logging.info(".NET runtime initialized successfully")
        return clr
    except Exception as e:
        logging.error(f"Failed to initialize .NET runtime: {e}")
        raise

# Clean up .NET runtime
def cleanup_dotnet():
    try:
        import pythonnet
        logging.info("Cleaning up .NET runtime...")
        try:
            pythonnet.load("coreclr")
            pythonnet.unload()
            logging.info(".NET runtime cleanup completed")
        except Exception as e:
            logging.warning(f"Runtime cleanup warning: {e}")
    except Exception as e:
        logging.error(f"Error during .NET runtime cleanup: {e}")

# Register cleanup function
atexit.register(cleanup_dotnet)

# Initialize .NET runtime with retry
max_init_retries = 3
retry_delay = 2
clr = None

for init_attempt in range(max_init_retries):
    try:
        clr = initialize_dotnet()
        if clr is not None:
            break
    except Exception as e:
        if init_attempt == max_init_retries - 1:
            raise Exception(f"Failed to initialize .NET runtime after {max_init_retries} attempts")
        logging.warning(f"Runtime initialization attempt {init_attempt + 1} failed: {e}")
        import time
        time.sleep(retry_delay)

# Add references to Thermo API assemblies
try:
    api_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'lib', 'Exploris4.3-and-higher')
    logging.info(f"Loading assemblies from: {api_dir}")
    
    # Add the API directory to system path
    if api_dir not in sys.path:
        sys.path.append(api_dir)
    
    # Load required assemblies
    clr.AddReference('System')
    clr.AddReference(os.path.join(api_dir, 'Thermo.API.Exploris.NetStd-1.0'))
    clr.AddReference(os.path.join(api_dir, 'Thermo.API.NetStd-1.0'))
    
    # Import required types
    from System import EventHandler, EventArgs
    from Thermo.Interfaces.ExplorisAccess_V1.Control.Acquisition import ExplorisAcquisitionOpeningEventArgs
    from Thermo.Interfaces.InstrumentAccess_V1.MsScanContainer import MsScanEventArgs

    logging.basicConfig(
        filename='mass_spec.log',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Add IAPI directory to Python path
    iapi_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    lib_dir = os.path.join(iapi_dir, 'lib')
    exploris_dir = os.path.join(lib_dir, 'Exploris4.3-and-higher')
    sys.path.append(iapi_dir)
    sys.path.append(lib_dir)
    sys.path.append(exploris_dir)

    # Import IAPI assemblies
    clr.AddReference(os.path.join(exploris_dir, 'Thermo.API.NetStd-1.0.dll'))
    clr.AddReference(os.path.join(exploris_dir, 'Thermo.API.Exploris.NetStd-1.0.dll'))
    clr.AddReference(os.path.join(exploris_dir, 'Thermo.API.Spectrum.NetStd-1.0.dll'))

    # Import required .NET types
    from System import Environment, IO
    from Microsoft.Win32 import Registry, RegistryKey, RegistryHive, RegistryView
    from System.Xml import XmlDocument
    from System.Reflection import Assembly

    from Thermo.Interfaces.ExplorisAccess_V1 import IExplorisInstrumentAccess, IExplorisInstrumentAccessContainer
    from Thermo.Interfaces.ExplorisAccess_V1.Control.Acquisition import ExplorisAcquisitionOpeningEventArgs
    from Thermo.Interfaces.ExplorisAccess_V1.MsScanContainer import IExplorisMsScan
    from Thermo.Interfaces.InstrumentAccess_V1.MsScanContainer import MsScanEventArgs
    
except Exception as e:
    logging.error(f"Failed to load Thermo API assemblies: {e}")
    # Continue execution in mock mode if assemblies fail to load
    pass

def get_api_instance():
    """Create an instance of the API object and return it."""
    logging.info("Starting get_api_instance()")
    DEFAULT_BASE_PATH = "Thermo\\Exploris"
    DEFAULT_REGISTRY = "SOFTWARE\\Thermo Exploris"
    XML_ROOT = "DataSystem"
    API_FILENAME_DESCRIPTOR = "ApiFileName"
    API_CLASSNAME_DESCRIPTOR = "ApiClassName"

    # Check registry first
    base_path = None
    key = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)
    merkur = key.OpenSubKey(DEFAULT_REGISTRY)
    if merkur is not None:
        base_path = merkur.GetValue("data", None)
        merkur.Dispose()
    key.Dispose()

    # If not found in registry, use default path
    if base_path is None or not IO.File.Exists(IO.Path.Combine(base_path, XML_ROOT + ".xml")):
        base_path = IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), DEFAULT_BASE_PATH)

    # Load XML configuration
    doc = XmlDocument()
    doc.Load(IO.Path.Combine(base_path, XML_ROOT + ".xml"))
    filename = doc[XML_ROOT][API_FILENAME_DESCRIPTOR].InnerText.strip()
    classname = doc[XML_ROOT][API_CLASSNAME_DESCRIPTOR].InnerText.strip()

    # Create API instance
    if not IO.File.Exists(filename):
        # Try GAC specification
        return Assembly.Load(filename).CreateInstance(classname)
    return Assembly.LoadFrom(filename).CreateInstance(classname)

# Removed eventlet imports - using threading mode instead

app = Flask(__name__)
CORS(app)

# Configure Socket.IO with threading
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)

# Queue to store scan data for SSE clients
scan_data_queue = queue.Queue(maxsize=100)
# Remote endpoint configuration
REMOTE_ENDPOINT = None  # Set this to your remote service URL, e.g., "https://your-relay-service.com/api/data"
REMOTE_API_KEY = None   # Set this to your API key if your remote service requires authentication

# Default scan data structure
DEFAULT_SCAN_DATA = {
    "timestamp": "",
    "scan_number": 0,
    "tic": 0.0,
    "base_peak_mass": 0.0,
    "base_peak_intensity": 0.0,
    "masses": [],
    "intensities": []
}

class MassSpectrometer:
    def __init__(self, mock_mode=False):
        logging.info("Initializing MassSpectrometer")
        # Initialize Exploris device
        self.container = None
        self.instrument = None
        self.orbitrap = None
        self.scan_data = DEFAULT_SCAN_DATA.copy()
        self.acquisition_start_time = None
        self.opening_handler = None
        self.closing_handler = None
        self.scan_handler = None
        self.lock = Lock()
        self.heartbeat_thread = None
        self.is_running = True
        self.mock_mode = mock_mode
        self.mock_connected = False
        self.mock_online_access = False
        self.mock_acquisition_active = False
        self.mock_scan_counter = 0
        

        
        try:
            if mock_mode:
                self._initialize_mock_instrument()
            else:
                self._initialize_instrument()
            self._start_heartbeat()
        except Exception as e:
            logging.error(f"Initialization error: {e}")
            if not mock_mode:
                logging.info("Falling back to mock mode...")
                self.mock_mode = True
                self._initialize_mock_instrument()
                self._start_heartbeat()
            else:
                self.cleanup()
                raise
    
    def _start_heartbeat(self):
        """Start a heartbeat thread to monitor instrument connection"""
        def heartbeat():
            while self.is_running:
                try:
                    if self.instrument and hasattr(self.instrument, 'IsConnected'):
                        if not self.instrument.IsConnected:
                            logging.warning("Instrument connection lost, attempting to reconnect...")
                            self._initialize_instrument()
                    time.sleep(5)  # Check every 5 seconds
                except Exception as e:
                    logging.error(f"Heartbeat error: {e}")
                    time.sleep(5)  # Wait before next check
        
        self.heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        self.heartbeat_thread.start()
    
    def _initialize_mock_instrument(self):
        """Initialize a mock instrument for testing when no physical instrument is available"""
        logging.info("Initializing mock instrument...")
        self.mock_connected = True
        self.mock_online_access = True
        self.mock_acquisition_active = False
        self.mock_scan_counter = 0
        
        # Generate some mock scan data
        import random
        import numpy as np
        
        # Create realistic mass spectrum data
        masses = np.linspace(100, 1000, 100)
        intensities = np.random.exponential(1000, 100) * np.random.random(100)
        
        self.scan_data = {
            "timestamp": datetime.now().isoformat(),
            "scan_number": 1,
            "tic": float(np.sum(intensities)),
            "base_peak_mass": float(masses[np.argmax(intensities)]),
            "base_peak_intensity": float(np.max(intensities)),
            "masses": masses.tolist(),
            "intensities": intensities.tolist()
        }
        
        logging.info("Mock instrument initialized successfully")
    
    def _start_mock_data_generation(self):
        """Start generating mock scan data periodically"""
        def generate_mock_scan():
            while self.is_running and self.mock_mode and self.mock_acquisition_active:
                try:
                    import random
                    import numpy as np
                    
                    # Generate realistic mass spectrum data with some variation
                    masses = np.linspace(100, 1000, 100)
                    base_intensities = np.random.exponential(1000, 100) * np.random.random(100)
                    # Add some noise and variation
                    intensities = base_intensities * (0.8 + 0.4 * np.random.random(100))
                    
                    self.mock_scan_counter += 1
                    
                    with self.lock:
                        self.scan_data = {
                            "timestamp": datetime.now().isoformat(),
                            "scan_number": self.mock_scan_counter,
                            "tic": float(np.sum(intensities)),
                            "base_peak_mass": float(masses[np.argmax(intensities)]),
                            "base_peak_intensity": float(np.max(intensities)),
                            "masses": masses.tolist(),
                            "intensities": intensities.tolist()
                        }
                    
                    # Emit scan data via WebSocket
                    socketio.emit('scan_data', self.scan_data)
                    
                    time.sleep(1)  # Generate new scan every second
                except Exception as e:
                    logging.error(f"Error generating mock scan data: {e}")
                    time.sleep(1)
        
        mock_thread = threading.Thread(target=generate_mock_scan, daemon=True)
        mock_thread.start()
    
    def _initialize_instrument(self):
        """Initialize the instrument connection with retry mechanism and detailed logging"""
        try:
            # Create API instance with retry
            logging.info("Getting API instance...")
            max_retries = 5
            retry_delay = 3  # seconds
            
            for attempt in range(max_retries):
                try:
                    logging.info(f"\n=== Initialization Attempt {attempt + 1} ===")
                    self.container = get_api_instance()
                    logging.debug(f"Container type: {type(self.container)}")
                    
                    if isinstance(self.container, IExplorisInstrumentAccessContainer):
                        logging.info("API instance created successfully")
                        break
                    logging.warning("Invalid container type returned, retrying...")
                    
                except Exception as e:
                    logging.error(f"=== Attempt {attempt + 1} failed: {str(e)} ===")
                    if attempt < max_retries - 1:
                        logging.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logging.error("Max retries reached. Failed to create API instance")
                        raise Exception(f"Failed to create API instance after {max_retries} attempts: {e}")
            
            # Start online access following the pattern from working examples
            logging.info("Starting online access...")
            self.container.StartOnlineAccess()
            
            # Wait for service connection following the example pattern
            logging.info("Waiting for service connection...")
            max_wait_time = 30  # seconds
            start_time = datetime.now()
            
            while not self.container.ServiceConnected:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > max_wait_time:
                    raise Exception(f"Service connection timeout after {max_wait_time} seconds")
                
                logging.info(f"Waiting for service connection... ({elapsed:.1f}s)")
                time.sleep(0.5)
            
            logging.info("Service connection established successfully")
            
            # Now try to get instrument IDs
            logging.info("Getting instrument IDs...")
            instrument_ids = None
            
            for attempt in range(max_retries):
                try:
                    logging.info(f"Attempt {attempt + 1} of {max_retries} to get instrument IDs...")
                    instrument_ids = self.container.GetInstrumentIds()
                    
                    if not instrument_ids:
                        raise Exception("GetInstrumentIds returned None")
                    
                    if len(instrument_ids) == 0:
                        raise Exception("No instruments found")
                    
                    logging.info(f"Found {len(instrument_ids)} instrument(s)")
                    break
                    
                except Exception as e:
                    logging.error(f"Failed to get instrument IDs (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        logging.info(f"Waiting {retry_delay} seconds before retry...")
                        time.sleep(retry_delay)
                    else:
                        raise Exception(f"Failed to get instrument IDs after {max_retries} attempts: {e}")
            
            if not instrument_ids:
                raise Exception("Failed to get instrument IDs: No valid response received")
            
            # Get first available instrument with retry
            logging.info("Getting instrument...")
            if not instrument_ids or len(instrument_ids) == 0:
                raise Exception("No instrument IDs available")
            
            logging.info(f"Attempting to connect to instrument ID: {instrument_ids[0]}")
            connection_success = False
            
            for attempt in range(max_retries):
                try:
                    logging.info(f"Attempt {attempt + 1} of {max_retries} to connect to instrument...")
                    self.instrument = self.container.Get(instrument_ids[0])
                    
                    if self.instrument is None:
                        raise Exception("Get() returned None for instrument")
                    
                    logging.info(f"Got instrument object, name: {self.instrument.InstrumentName if hasattr(self.instrument, 'InstrumentName') else 'Unknown'}")
                    logging.info("Instrument connection established successfully")
                    connection_success = True
                    break
                        
                except Exception as e:
                    logging.error(f"Instrument connection attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        logging.info(f"Waiting {retry_delay} seconds before retry...")
                        time.sleep(retry_delay)
                    else:
                        raise Exception(f"Failed to establish stable instrument connection after {max_retries} attempts: {e}")
            
            if not connection_success:
                raise Exception("Failed to establish stable instrument connection")
            
            logging.info("Instrument connection established successfully")
            
            # Get Orbitrap detector
            logging.info("Getting Orbitrap detector...")
            try:
                self.orbitrap = self.instrument.GetMsScanContainer(0)
                if self.orbitrap is None:
                    raise Exception("Failed to get MS scan container")
                logging.info(f"Connected to detector: {self.orbitrap.DetectorClass}")
            except Exception as e:
                logging.error(f"Failed to get Orbitrap detector: {e}")
                raise
            
            logging.info("Setting up event handlers...")
            try:
                # Unregister any existing handlers first
                if hasattr(self, 'opening_handler') and self.opening_handler is not None:
                    self.instrument.Control.Acquisition.AcquisitionStreamOpening -= self.opening_handler
                if hasattr(self, 'closing_handler') and self.closing_handler is not None:
                    self.instrument.Control.Acquisition.AcquisitionStreamClosing -= self.closing_handler
                if hasattr(self, 'scan_handler') and self.scan_handler is not None:
                    self.orbitrap.MsScanArrived -= self.scan_handler
                
                # Create and register event handlers
                try:
                    # Create delegates
                    self.opening_handler = EventHandler[ExplorisAcquisitionOpeningEventArgs](self.on_acquisition_stream_opening)
                    self.closing_handler = EventHandler[EventArgs](self.on_acquisition_stream_closing)
                    
                    # Register event handlers
                    self.instrument.Control.Acquisition.AcquisitionStreamOpening += self.opening_handler
                    logging.info("Registered opening handler")
                    
                    self.instrument.Control.Acquisition.AcquisitionStreamClosing += self.closing_handler
                    logging.info("Registered closing handler")
                    
                    # Create a proper delegate for the scan handler
                    def scan_handler(sender, args):
                        self.on_scan_arrived(sender, args)
                    
                    self.scan_handler = scan_handler
                    self.orbitrap.MsScanArrived += self.scan_handler
                    logging.info("Registered scan handler")
                    
                except Exception as e:
                    logging.error(f"Failed to register event handlers: {e}")
                    raise
                
                logging.info("Event handlers set up successfully")
            except Exception as e:
                logging.error(f"Error setting up event handlers: {e}")
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")
                raise
        except Exception as e:
            logging.error(f"Error initializing mass spectrometer: {e}")
            import traceback
            logging.error("Traceback:")
            logging.error(traceback.format_exc())
            self.cleanup()

    def on_acquisition_stream_opening(self, sender: object, args: ExplorisAcquisitionOpeningEventArgs) -> None:
        """Handle acquisition stream opening event"""
        try:
            logging.info("Acquisition stream opening event received")
            with self.lock:
                self.acquisition_start_time = datetime.now()
                self.scan_data = DEFAULT_SCAN_DATA.copy()
            logging.info("Acquisition stream opening event handled successfully")
            return None
        except Exception as e:
            logging.error(f"Error in acquisition stream opening handler: {e}")
            return None

    def on_acquisition_stream_closing(self, sender: object, args: EventArgs) -> None:
        """Handle acquisition stream closing event"""
        try:
            logging.info("Acquisition stream closing event received")
            with self.lock:
                self.acquisition_start_time = None
            logging.info("Acquisition stream closing event handled successfully")
            return None
        except Exception as e:
            logging.error(f"Error in acquisition stream closing handler: {e}")
            return None

    def on_scan_arrived(self, sender: object, args: MsScanEventArgs) -> None:
        """Handle scan arrival events from the mass spectrometer."""
        try:
            logging.info("Processing scan arrived event...")
            
            # Check if args is valid
            if args is None:
                logging.error("Scan event args is None")
                return

            # Get scan using GetScan() method and use 'using' pattern for proper disposal
            scan = args.GetScan()
            if scan is None:
                logging.error("Failed to get scan from args")
                return
                
            try:
                # Extract scan metadata
                ms_order = 1  # Default to MS1
                polarity = "Unknown"  # Default polarity
                
                if hasattr(scan, 'Header') and scan.Header:
                    try:
                        # Try to get MSOrder from header
                        try:
                            ms_order = int(scan.Header['MSOrder'])
                        except (KeyError, Exception):
                            pass  # Keep default value
                        
                        # Try to get Polarity from header
                        try:
                            polarity_value = scan.Header['Polarity']
                            # Convert polarity value to readable format
                            if polarity_value == "0" or polarity_value.lower() == "positive":
                                polarity = "Positive"
                            elif polarity_value == "1" or polarity_value.lower() == "negative":
                                polarity = "Negative"
                            else:
                                polarity = polarity_value
                        except (KeyError, Exception):
                            pass  # Keep default value
                        
                        logging.info(f"MS Order: {ms_order}, Polarity: {polarity}")
                    except Exception as e:
                        logging.warning(f"Could not parse scan metadata: {e}")
                

                
                # Use a simple counter for scan numbering since IMsScan doesn't have RunningNumber
                if not hasattr(self, 'scan_counter'):
                    self.scan_counter = 0
                self.scan_counter += 1
                scan_number = self.scan_counter
                logging.info(f"Processing MS1 scan number: {scan_number}")
                logging.info(f"Centroid count: {scan.CentroidCount}")
                
                # Extract masses and intensities
                masses = []
                intensities = []
                
                # Access centroid data
                for centroid in scan.Centroids:
                    masses.append(float(centroid.Mz))
                    intensities.append(float(centroid.Intensity))
                
                logging.info(f"Extracted {len(masses)} data points")
                
                # Create scan data dictionary
                scan_data = {
                    'scan_number': int(scan_number),
                    'masses': masses,
                    'intensities': intensities,
                    'centroid_count': scan.CentroidCount,
                    'ms_order': ms_order,
                    'polarity': polarity,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Update internal scan data
                with self.lock:
                    self.scan_data = scan_data
                
                # Emit data via WebSocket
                socketio.emit('scan_data', scan_data)
                
                # Add to SSE queue (non-blocking, drop if queue is full)
                try:
                    if 'scan_data_queue' in globals():
                        try:
                            scan_data_queue.put_nowait(scan_data)
                        except queue.Full:
                            # If queue is full, remove oldest item and add new one
                            try:
                                scan_data_queue.get_nowait()
                                scan_data_queue.put_nowait(scan_data)
                            except Exception:
                                pass
                except Exception as e:
                    logging.error(f"Error adding data to SSE queue: {e}")
                
                # Push to remote endpoint if configured
                if 'REMOTE_ENDPOINT' in globals() and REMOTE_ENDPOINT:
                    # Use a thread to avoid blocking the scan handler
                    threading.Thread(target=push_to_remote, args=(scan_data,), daemon=True).start()
                    
                logging.info("Successfully emitted scan data...")
                
            finally:
                # Dispose the scan object to free shared memory
                if hasattr(scan, 'Dispose'):
                    scan.Dispose()
            
        except Exception as e:
            logging.error(f"Error in on_scan_arrived: {str(e)}")
            logging.error(f"Error type: {type(e).__name__}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")

    def get_current_scan_data(self):
        """Get the current scan data"""
        with self.lock:
            return self.scan_data.copy()

    def cleanup(self):
        """Cleanup resources"""
        logging.info("Starting cleanup...")
        try:
            # Stop the heartbeat thread
            self.is_running = False
            if hasattr(self, 'heartbeat_thread') and self.heartbeat_thread and self.heartbeat_thread.is_alive():
                try:
                    self.heartbeat_thread.join(timeout=5)
                    if self.heartbeat_thread.is_alive():
                        logging.warning("Heartbeat thread did not terminate gracefully")
                except Exception as e:
                    logging.error(f"Error stopping heartbeat thread: {e}")
            
            # Cleanup instrument resources
            if hasattr(self, 'instrument') and self.instrument is not None:
                try:
                    # Check if Control and Acquisition are available
                    if hasattr(self.instrument, 'Control') and hasattr(self.instrument.Control, 'Acquisition'):
                        if self.opening_handler is not None:
                            try:
                                self.instrument.Control.Acquisition.AcquisitionStreamOpening -= self.opening_handler
                                logging.info("Removed opening handler")
                            except Exception as e:
                                logging.error(f"Error removing opening handler: {e}")
                        
                        if self.closing_handler is not None:
                            try:
                                self.instrument.Control.Acquisition.AcquisitionStreamClosing -= self.closing_handler
                                logging.info("Removed closing handler")
                            except Exception as e:
                                logging.error(f"Error removing closing handler: {e}")
                    
                    if self.scan_handler is not None and self.orbitrap is not None:
                        try:
                            self.orbitrap.MsScanArrived -= self.scan_handler
                            logging.info("Removed scan handler")
                        except Exception as e:
                            logging.error(f"Error removing scan handler: {e}")
                    
                    # Note: StopOnlineAccess is not available in this API version
                    # The connection will be cleaned up when the container is disposed
                except Exception as e:
                    logging.error(f"Error during instrument cleanup: {e}")
                finally:
                    self.instrument = None
            
            # Reset other resources
            self.container = None
            self.orbitrap = None
            self.opening_handler = None
            self.closing_handler = None
            self.scan_handler = None

            self.scan_data = DEFAULT_SCAN_DATA.copy()
            self.acquisition_start_time = None
            
            logging.info("Cleanup completed")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
            raise

    def __del__(self):
        self.cleanup()

# Initialize mass spectrometer in mock mode by default
# This allows the GUI to work even without a physical instrument
mass_spec = MassSpectrometer(mock_mode=False)

@app.route('/status', methods=['GET'])
def get_status():
    try:
        if mass_spec.mock_mode:
            status = {
                "instrument_connected": mass_spec.mock_connected,
                "online_access": mass_spec.mock_online_access,
                "acquisition_active": mass_spec.mock_acquisition_active,
                "timestamp": datetime.now().isoformat(),
                "mock_mode": True
            }
        else:
            status = {
                "instrument_connected": mass_spec.instrument is not None,
                "online_access": False,
                "acquisition_active": False,
                "timestamp": datetime.now().isoformat(),
                "mock_mode": False
            }
            
            if mass_spec.instrument and mass_spec.instrument.Control:
                try:
                    status["online_access"] = mass_spec.container.ServiceConnected if hasattr(mass_spec, 'container') else False
                    # Check if acquisition is running by examining the state
                    if hasattr(mass_spec.instrument.Control, 'Acquisition'):
                        state = mass_spec.instrument.Control.Acquisition.State
                        status["acquisition_active"] = str(state.SystemState) == "Running" if hasattr(state, 'SystemState') else False
                    else:
                        status["acquisition_active"] = False
                except Exception as e:
                    logging.error(f"Error getting instrument status: {e}")
        
        return jsonify({"success": True, "status": status})
    except Exception as e:
        logging.error(f"Error getting status: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/scan_data', methods=['GET'])
def get_scan_data():
    try:
        scan_data = mass_spec.get_current_scan_data()
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

@app.route('/start_acquisition', methods=['POST'])
def start_acquisition():
    try:
        if mass_spec.mock_mode:
            if mass_spec.mock_acquisition_active:
                return jsonify({
                    "success": False,
                    "error": "Acquisition already active",
                    "timestamp": datetime.now().isoformat()
                })
            
            mass_spec.mock_acquisition_active = True
            mass_spec.acquisition_start_time = datetime.now()
            
            # Start mock data generation
            mass_spec._start_mock_data_generation()
            
            return jsonify({
                "success": True,
                "message": "Mock acquisition started",
                "timestamp": datetime.now().isoformat()
            })
        else:
            if not mass_spec.instrument or not mass_spec.instrument.Control:
                raise Exception("Instrument not connected or control not available")
                
            if not (hasattr(mass_spec, 'container') and mass_spec.container.ServiceConnected):
                raise Exception("Service connection not active")
                
            # Check if acquisition is already running
            state = mass_spec.instrument.Control.Acquisition.State
            if hasattr(state, 'SystemState') and str(state.SystemState) == "Running":
                return jsonify({
                    "success": False,
                    "error": "Acquisition already active",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Start acquisition using CreatePermanentAcquisition
            workflow = mass_spec.instrument.Control.Acquisition.CreatePermanentAcquisition()
            mass_spec.instrument.Control.Acquisition.StartAcquisition(workflow)
            mass_spec.acquisition_start_time = datetime.now()
            
            return jsonify({
                "success": True,
                "message": "Acquisition started",
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        logging.error(f"Error starting acquisition: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/stop_acquisition', methods=['POST'])
def stop_acquisition():
    try:
        if mass_spec.mock_mode:
            if not mass_spec.mock_acquisition_active:
                return jsonify({
                    "success": False,
                    "error": "No acquisition active",
                    "timestamp": datetime.now().isoformat()
                })
            
            mass_spec.mock_acquisition_active = False
            mass_spec.acquisition_start_time = None
            
            return jsonify({
                "success": True,
                "message": "Mock acquisition stopped",
                "timestamp": datetime.now().isoformat()
            })
        else:
            if not mass_spec.instrument or not mass_spec.instrument.Control:
                raise Exception("Instrument not connected or control not available")
                
            if not (hasattr(mass_spec, 'container') and mass_spec.container.ServiceConnected):
                raise Exception("Service connection not active")
                
            # Cancel the acquisition
            mass_spec.instrument.Control.Acquisition.CancelAcquisition()
            return jsonify({
                "success": True,
                "message": "Acquisition stopped",
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        logging.error(f"Error stopping acquisition: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500



def shutdown_server():
    # ADDED: Logging for shutdown sequence
    logging.info("shutdown_server() called.")
    logging.info("Starting cleanup...")
    try:
        # Clean up mass spectrometer
        if hasattr(app, 'mass_spec'):
            app.mass_spec.cleanup()
        logging.info("Mass spectrometer cleanup completed")
        
        # Clean up .NET runtime
        cleanup_dotnet()
        
        logging.info("Server shutdown complete")
        
    except Exception as e:
        logging.error(f"Error during shutdown: {e}")

def signal_handler(sig, frame):
    logging.info("Received shutdown signal")
    shutdown_server()
    sys.exit(0)

@app.route('/events')
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



@app.route('/events')
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

def push_to_remote(data):
    """Push scan data to a remote endpoint"""
    if not REMOTE_ENDPOINT:
        return
    
    try:
        headers = {}
        if REMOTE_API_KEY:
            headers['Authorization'] = f'Bearer {REMOTE_API_KEY}'
        
        response = requests.post(
            REMOTE_ENDPOINT,
            json=data,
            headers=headers,
            timeout=5  # 5 second timeout
        )
        
        if response.status_code != 200:
            logging.error(f"Failed to push data to remote endpoint: {response.status_code} {response.text}")
    except Exception as e:
        logging.error(f"Error pushing data to remote endpoint: {e}")