import logging
import clr
import os
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG)

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
    
    logging.info("Successfully loaded all required assemblies and types")
except Exception as e:
    logging.error(f"Error loading assemblies: {e}")
    raise

class ThermoAPI:
    def __init__(self):
        self.acquisition_stream_opening = None
        self.acquisition_stream_closing = None
        self.scan_arrived = None
        logging.info("ThermoAPI instance initialized")

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        """Clean up resources and event handlers"""
        try:
            logging.info("Starting cleanup...")
            if hasattr(self, 'acquisition_stream_opening') and self.acquisition_stream_opening is not None:
                self.acquisition_stream_opening = None
            if hasattr(self, 'acquisition_stream_closing') and self.acquisition_stream_closing is not None:
                self.acquisition_stream_closing = None
            if hasattr(self, 'scan_arrived') and self.scan_arrived is not None:
                self.scan_arrived = None
            logging.info("Cleanup completed")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")