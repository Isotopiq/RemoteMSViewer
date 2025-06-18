#!/usr/bin/env python3
"""
ThermoAPI Web Viewer Server Manager GUI
A graphical interface to start, stop, and monitor the backend and frontend servers.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import time
import os
import sys
import psutil
import requests
from pathlib import Path

class ServerManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ThermoAPI Server Manager")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Get script directory
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            self.script_dir = Path(sys.executable).parent
        else:
            # Running as script
            self.script_dir = Path(__file__).parent
            
        self.backend_dir = self.script_dir / "backend"
        self.frontend_dir = self.script_dir / "frontend"
        
        # Server process tracking
        self.backend_process = None
        self.frontend_process = None
        self.backend_monitor_thread = None
        self.monitoring = False
        
        # Create GUI
        self.create_widgets()
        
        # Start monitoring thread
        self.start_monitoring()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="ThermoAPI Server Manager", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Server status frame
        status_frame = ttk.LabelFrame(main_frame, text="Server Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # Backend status
        ttk.Label(status_frame, text="Backend Server:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.backend_status_label = ttk.Label(status_frame, text="Stopped", foreground="red")
        self.backend_status_label.grid(row=0, column=1, sticky=tk.W)
        self.backend_url_label = ttk.Label(status_frame, text="", foreground="blue")
        self.backend_url_label.grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        
        # Frontend status
        ttk.Label(status_frame, text="Frontend Server:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.frontend_status_label = ttk.Label(status_frame, text="Stopped", foreground="red")
        self.frontend_status_label.grid(row=1, column=1, sticky=tk.W)
        self.frontend_url_label = ttk.Label(status_frame, text="", foreground="blue")
        self.frontend_url_label.grid(row=1, column=2, sticky=tk.W, padx=(10, 0))
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10))
        
        # Start/Stop buttons
        self.start_button = ttk.Button(control_frame, text="Start Servers", 
                                      command=self.start_servers, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Servers", 
                                     command=self.stop_servers)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_button = ttk.Button(control_frame, text="Refresh Status", 
                                        command=self.refresh_status)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_button = ttk.Button(control_frame, text="Test Backend", 
                                     command=self.test_backend)
        self.test_button.pack(side=tk.LEFT)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Server Logs", padding="10")
        log_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        clear_button = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_button.grid(row=1, column=0, pady=(5, 0))
        
    def log_message(self, message):
        """Add a message to the log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Update GUI in main thread
        self.root.after(0, self._update_log, log_entry)
        
    def _update_log(self, log_entry):
        """Update log text widget (must be called from main thread)"""
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def clear_log(self):
        """Clear the log text area"""
        self.log_text.delete(1.0, tk.END)
        
    def check_port(self, port):
        """Check if a port is in use"""
        try:
            for conn in psutil.net_connections(kind='inet'):
                if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == port:
                    if hasattr(conn, 'status') and conn.status == psutil.CONN_LISTEN:
                        return True
        except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
            pass
        return False
        
    def check_server_health(self, url):
        """Check if server is responding"""
        try:
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except:
            return False
            
    def update_server_status(self):
        """Update server status indicators"""
        # Check backend (port 5000)
        backend_running = self.check_port(5000)
        if backend_running:
            self.backend_status_label.config(text="Running", foreground="green")
            self.backend_url_label.config(text="http://localhost:5000")
        else:
            self.backend_status_label.config(text="Stopped", foreground="red")
            self.backend_url_label.config(text="")
            
        # Check frontend (ports 3000-3001)
        frontend_running = False
        frontend_port = None
        for port in [3000, 3001]:
            if self.check_port(port):
                frontend_running = True
                frontend_port = port
                break
                
        if frontend_running:
            self.frontend_status_label.config(text="Running", foreground="green")
            self.frontend_url_label.config(text=f"http://localhost:{frontend_port}")
        else:
            self.frontend_status_label.config(text="Stopped", foreground="red")
            self.frontend_url_label.config(text="")
            
    def ensure_backend_dependencies(self, python_cmd):
        """Ensure backend dependencies are installed"""
        try:
            self.log_message(f"Checking dependencies for {python_cmd}...")
            
            # List of required packages
            required_packages = [
                'flask',
                'flask_cors', 
                'flask_socketio',
                'pythonnet',
                'gevent',
                'numpy'
            ]
            
            # Check if packages are available
            missing_packages = []
            for package in required_packages:
                try:
                    result = subprocess.run(
                        [python_cmd, "-c", f"import {package}"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode != 0:
                        missing_packages.append(package)
                except Exception:
                    missing_packages.append(package)
            
            if missing_packages:
                self.log_message(f"Missing packages: {', '.join(missing_packages)}")
                self.log_message("Installing missing dependencies...")
                
                # Install packages using pip
                try:
                    install_result = subprocess.run(
                        [python_cmd, "-m", "pip", "install"] + [
                            "flask>=2.0.0",
                            "flask-cors>=4.0.0", 
                            "flask-socketio>=5.3.0",
                            "pythonnet>=3.0.1",
                            "gevent",
                            "numpy"
                        ],
                        capture_output=True,
                        text=True,
                        timeout=120,
                        cwd=str(self.backend_dir)
                    )
                    
                    if install_result.returncode == 0:
                        self.log_message("Dependencies installed successfully")
                        return True
                    else:
                        self.log_message(f"Failed to install dependencies: {install_result.stderr}")
                        return False
                        
                except subprocess.TimeoutExpired:
                    self.log_message("Dependency installation timed out")
                    return False
                except Exception as e:
                    self.log_message(f"Error installing dependencies: {e}")
                    return False
            else:
                self.log_message("All dependencies are available")
                return True
                
        except Exception as e:
            self.log_message(f"Error checking dependencies: {e}")
            return False
    
    def start_servers(self):
        """Start both servers with simplified backend startup"""
        def start_thread():
            try:
                self.log_message("Starting servers...")
                
                # Check if directories exist
                if not self.backend_dir.exists():
                    self.log_message(f"Error: Backend directory not found: {self.backend_dir}")
                    return
                    
                if not self.frontend_dir.exists():
                    self.log_message(f"Error: Frontend directory not found: {self.frontend_dir}")
                    return
                
                # Start backend
                self.log_message("Starting backend server...")
                
                # Try different Python commands
                python_commands = ["python", "python.exe", "py", "py.exe"]
                
                backend_started = False
                
                for python_cmd in python_commands:
                    try:
                        self.log_message(f"Trying to start backend with {python_cmd}...")
                        
                        # First test if the python command works
                        test_process = subprocess.run(
                            [python_cmd, "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        if test_process.returncode != 0:
                            self.log_message(f"{python_cmd} not available")
                            continue
                            
                        self.log_message(f"Using {python_cmd} (version: {test_process.stdout.strip()})")
                        
                        # Start the backend server directly without dependency checking
                        # In the start_servers function, add more debugging
                        self.backend_process = subprocess.Popen(
                            [python_cmd, "main.py"],
                            cwd=str(self.backend_dir),  # This should be the backend directory
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            bufsize=1,
                            universal_newlines=True,
                            env=os.environ.copy()  # Add this line to ensure environment variables are passed
                        )
                        
                        # Wait a moment and check if process is still running
                        time.sleep(3)
                        if self.backend_process.poll() is None:
                            self.log_message(f"Backend server started successfully with {python_cmd}")
                            # Try to read some initial output
                            try:
                                # Check if there's any immediate output
                                import select
                                import sys
                                if sys.platform == 'win32':
                                    # On Windows, just log success
                                    self.log_message("Backend process is running")
                                else:
                                    # On Unix-like systems, we can use select
                                    ready, _, _ = select.select([self.backend_process.stdout], [], [], 1)
                                    if ready:
                                        output = self.backend_process.stdout.readline()
                                        if output:
                                            self.log_message(f"Backend output: {output.strip()}")
                            except Exception as e:
                                self.log_message(f"Note: Could not read backend output: {e}")
                            
                            backend_started = True
                            
                            # Start monitoring backend output
                            self.start_backend_monitoring()
                            break
                        else:
                            # Process exited, get error output
                            try:
                                stdout, stderr = self.backend_process.communicate(timeout=5)
                                self.log_message(f"Backend failed with {python_cmd} (exit code: {self.backend_process.returncode}):")
                                if stdout:
                                    self.log_message(f"STDOUT: {stdout}")
                                if stderr:
                                    self.log_message(f"STDERR: {stderr}")
                            except subprocess.TimeoutExpired:
                                self.log_message(f"Backend process with {python_cmd} timed out during error collection")
                                self.backend_process.kill()
                                stdout, stderr = self.backend_process.communicate()
                                if stdout:
                                    self.log_message(f"STDOUT: {stdout}")
                                if stderr:
                                    self.log_message(f"STDERR: {stderr}")
                            
                    except subprocess.TimeoutExpired:
                        self.log_message(f"{python_cmd} command timed out")
                        continue
                    except FileNotFoundError:
                        self.log_message(f"{python_cmd} not found in PATH")
                        continue
                    except Exception as e:
                        self.log_message(f"Failed to start backend with {python_cmd}: {e}")
                        continue
                
                if not backend_started:
                    self.log_message("Failed to start backend server with any Python command")
                    return
                
                # Wait a moment for backend to initialize
                time.sleep(3)
                
                # Start frontend
                self.log_message("Starting frontend server...")
                try:
                    # Try different npm commands for Windows
                    npm_commands = ["npm", "npm.cmd", "npm.exe"]
                    npm_found = False
                    
                    for npm_cmd in npm_commands:
                        try:
                            self.frontend_process = subprocess.Popen(
                                [npm_cmd, "run", "dev"],
                                cwd=str(self.frontend_dir),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                            )
                            npm_found = True
                            break
                        except FileNotFoundError:
                            continue
                    
                    if npm_found:
                        self.log_message("Frontend server started")
                    else:
                        self.log_message("Failed to start frontend: npm not found. Please install Node.js and npm.")
                        return
                        
                except Exception as e:
                    self.log_message(f"Failed to start frontend: {e}")
                    return
                    
                self.log_message("Both servers started successfully!")
                
            except Exception as e:
                self.log_message(f"Error starting servers: {e}")
                
        # Run in separate thread to avoid blocking GUI
        threading.Thread(target=start_thread, daemon=True).start()
        
    def stop_servers(self):
        """Stop both servers"""
        def stop_thread():
            try:
                self.log_message("Stopping servers...")
                
                # Stop processes if we have references
                if self.backend_process:
                    try:
                        self.backend_process.terminate()
                        self.log_message("Backend process terminated")
                    except:
                        pass
                        
                if self.frontend_process:
                    try:
                        self.frontend_process.terminate()
                        self.log_message("Frontend process terminated")
                    except:
                        pass
                
                # Kill processes by port (more thorough)
                killed_any = False
                for port in [5000, 3000, 3001]:
                    try:
                        for proc in psutil.process_iter(['pid', 'name']):
                            try:
                                # Get connections for this process
                                connections = proc.connections(kind='inet')
                                for conn in connections:
                                    if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == port:
                                        if hasattr(conn, 'status') and conn.status == psutil.CONN_LISTEN:
                                            proc.terminate()
                                            self.log_message(f"Terminated process on port {port} (PID: {proc.pid})")
                                            killed_any = True
                                            break
                            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
                                continue
                    except Exception as e:
                        self.log_message(f"Error checking port {port}: {e}")
                        
                if not killed_any:
                    self.log_message("No server processes found to stop")
                else:
                    self.log_message("Server shutdown complete")
                    
                # Stop backend monitoring
                if self.backend_monitor_thread and self.backend_monitor_thread.is_alive():
                    self.log_message("Stopping backend monitoring...")
                    # The monitoring thread will stop automatically when backend_process becomes None
                    
                # Clear process references
                self.backend_process = None
                self.frontend_process = None
                
            except Exception as e:
                self.log_message(f"Error stopping servers: {e}")
                
        # Run in separate thread
        threading.Thread(target=stop_thread, daemon=True).start()
        
    def refresh_status(self):
        """Manually refresh server status"""
        self.update_server_status()
        self.log_message("Status refreshed")
        
    def test_backend(self):
        """Run backend diagnostics test"""
        def test_thread():
            try:
                self.log_message("Running backend diagnostics...")
                
                # Run the test_backend.py script
                test_script = self.script_dir / "test_backend.py"
                
                if not test_script.exists():
                    self.log_message("Error: test_backend.py not found")
                    return
                
                # Try different Python commands
                python_commands = ["python", "python.exe", "py", "py.exe"]
                
                for python_cmd in python_commands:
                    try:
                        self.log_message(f"Running diagnostics with {python_cmd}...")
                        
                        result = subprocess.run(
                            [python_cmd, str(test_script)],
                            capture_output=True,
                            text=True,
                            timeout=30,
                            cwd=str(self.script_dir)
                        )
                        
                        if result.returncode == 0:
                            self.log_message("Backend diagnostics completed successfully:")
                            for line in result.stdout.split('\n'):
                                if line.strip():
                                    self.log_message(f"  {line}")
                            break
                        else:
                            self.log_message(f"Diagnostics failed with {python_cmd}:")
                            if result.stderr:
                                for line in result.stderr.split('\n'):
                                    if line.strip():
                                        self.log_message(f"  ERROR: {line}")
                            
                    except subprocess.TimeoutExpired:
                        self.log_message(f"Diagnostics timed out with {python_cmd}")
                        continue
                    except FileNotFoundError:
                        self.log_message(f"{python_cmd} not found")
                        continue
                    except Exception as e:
                        self.log_message(f"Error running diagnostics with {python_cmd}: {e}")
                        continue
                else:
                    self.log_message("Failed to run diagnostics with any Python command")
                    
            except Exception as e:
                self.log_message(f"Error running backend diagnostics: {e}")
        
        # Run in separate thread to avoid blocking GUI
        threading.Thread(target=test_thread, daemon=True).start()
    
    def start_backend_monitoring(self):
        """Start monitoring backend process output"""
        def monitor_backend_output():
            if not self.backend_process:
                return
                
            try:
                while self.backend_process and self.backend_process.poll() is None:
                    # Read stdout
                    if self.backend_process.stdout:
                        line = self.backend_process.stdout.readline()
                        if line:
                            self.root.after(0, lambda: self.log_message(f"Backend: {line.strip()}"))
                    
                    # Read stderr with Socket.IO noise filtering
                    if self.backend_process.stderr:
                        line = self.backend_process.stderr.readline()
                        if line:
                            line_stripped = line.strip()
                            # Filter out known Socket.IO noise
                            socketio_patterns = [
                                "Sending packet OPEN data",
                                "Received request to upgrade to websocket",
                                "Sending packet PONG data",
                                "Received packet PING",
                                "Received packet PONG",
                                "Client disconnected",
                                "Client connected"
                            ]
                            
                            is_socketio_noise = any(pattern in line_stripped for pattern in socketio_patterns)
                            
                            if is_socketio_noise:
                                # Log Socket.IO messages as info, not errors
                                self.root.after(0, lambda l=line_stripped: self.log_message(f"Backend Info: {l}"))
                            else:
                                # Log actual errors
                                self.root.after(0, lambda l=line_stripped: self.log_message(f"Backend Error: {l}"))
                    
                    time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                    
                # Process has ended
                if self.backend_process:
                    exit_code = self.backend_process.poll()
                    self.root.after(0, lambda: self.log_message(f"Backend process ended with exit code: {exit_code}"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Backend monitoring error: {e}"))
        
        # Start monitoring in a separate thread
        self.backend_monitor_thread = threading.Thread(target=monitor_backend_output, daemon=True)
        self.backend_monitor_thread.start()
        
    def start_monitoring(self):
        """Start the status monitoring thread"""
        def monitor_thread():
            self.monitoring = True
            while self.monitoring:
                try:
                    self.root.after(0, self.update_server_status)
                    time.sleep(2)  # Check every 2 seconds
                except:
                    break
                    
        threading.Thread(target=monitor_thread, daemon=True).start()
        
    def on_closing(self):
        """Handle window closing"""
        self.monitoring = False
        
        # Ask if user wants to stop servers
        if self.check_port(5000) or self.check_port(3000) or self.check_port(3001):
            result = messagebox.askyesno(
                "Stop Servers?", 
                "Servers are still running. Do you want to stop them before closing?"
            )
            if result:
                self.stop_servers()
                time.sleep(2)  # Give time for shutdown
                
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ServerManagerGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()