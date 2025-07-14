#!/usr/bin/env python3
"""
Network Monitor for Raspberry Pi Stats Broadcaster
Continuously monitors wlan0 interface for network connectivity
and automatically starts the stats broadcaster server when connected.
"""

import socket
import subprocess
import time
import logging
import signal
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NetworkMonitor:
    def __init__(self, interface='wlan0', check_interval=5, script_path='./start_server.sh'):
        self.interface = interface
        self.check_interval = check_interval
        self.script_path = script_path
        self.server_process = None
        self.is_connected = False
        self.last_ip = None
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self._stop_server()
        sys.exit(0)
    
    def get_interface_ip(self):
        """
        Get IP address of the specified network interface using socket module
        Returns IP address string if found, None otherwise
        """
        try:
            # Method 1: Using socket and connecting to get local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                
                # Verify this IP is actually on the wlan0 interface
                if self._verify_ip_on_interface(local_ip):
                    return local_ip
                    
        except Exception as e:
            logger.debug(f"Socket method failed: {e}")
        
        # Method 2: Parse ip command output
        try:
            result = subprocess.run(
                ['ip', 'addr', 'show', self.interface],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.split('\n'):
                if 'inet ' in line and 'scope global' in line:
                    ip_info = line.strip().split()
                    for item in ip_info:
                        if '/' in item and not item.startswith('inet'):
                            ip = item.split('/')[0]
                            if self._is_valid_ip(ip):
                                return ip
                                
        except subprocess.CalledProcessError as e:
            logger.debug(f"ip command failed: {e}")
        
        # Method 3: Using netifaces if available
        try:
            import netifaces
            
            if self.interface in netifaces.interfaces():
                addresses = netifaces.ifaddresses(self.interface)
                if netifaces.AF_INET in addresses:
                    for addr_info in addresses[netifaces.AF_INET]:
                        ip = addr_info.get('addr')
                        if ip and self._is_valid_ip(ip):
                            return ip
                            
        except ImportError:
            logger.debug("netifaces module not available")
        except Exception as e:
            logger.debug(f"netifaces method failed: {e}")
        
        return None
    
    def _verify_ip_on_interface(self, ip):
        """
        Verify that the given IP address is actually assigned to the target interface
        """
        try:
            result = subprocess.run(
                ['ip', 'addr', 'show', self.interface],
                capture_output=True,
                text=True,
                check=True
            )
            return ip in result.stdout
        except:
            return False
    
    def _is_valid_ip(self, ip):
        """
        Check if the IP address is valid and not a loopback address
        """
        try:
            socket.inet_aton(ip)
            return not ip.startswith('127.') and not ip.startswith('169.254.')
        except socket.error:
            return False
    
    def _is_server_running(self):
        """
        Check if the stats broadcaster server is already running
        """
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'stats_broadcaster.py'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def _start_server(self):
        """
        Start the stats broadcaster server
        """
        try:
            if self._is_server_running():
                logger.info("Server is already running")
                return True
            
            # Make sure the script is executable
            os.chmod(self.script_path, 0o755)
            
            # Start the server in the background
            self.server_process = subprocess.Popen(
                [self.script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if it's actually running
            if self._is_server_running():
                logger.info("Stats broadcaster server started successfully")
                return True
            else:
                logger.error("Failed to start stats broadcaster server")
                return False
                
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False
    
    def _stop_server(self):
        """
        Stop the stats broadcaster server
        """
        try:
            # Kill all processes matching the pattern
            subprocess.run(
                ['pkill', '-f', 'stats_broadcaster.py'],
                capture_output=True
            )
            
            # If we have a direct process handle, terminate it
            if self.server_process:
                try:
                    # Kill the entire process group
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGKILL)
                except:
                    pass
                finally:
                    self.server_process = None
            
            logger.info("Stats broadcaster server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping server: {e}")
    
    def _test_internet_connectivity(self):
        """
        Test if we can actually reach the internet
        """
        try:
            # Try to connect to Google's DNS
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect(("8.8.8.8", 53))
                return True
        except:
            return False
    
    def check_connection(self):
        """
        Check network connection status and manage server accordingly
        """
        current_ip = self.get_interface_ip()
        
        if current_ip:
            # Test actual internet connectivity
            if self._test_internet_connectivity():
                if not self.is_connected or current_ip != self.last_ip:
                    logger.info(f"Network connected: {current_ip}")
                    self.is_connected = True
                    self.last_ip = current_ip
                    
                    # Start server if not already running
                    if not self._is_server_running():
                        logger.info("Starting stats broadcaster server...")
                        self._start_server()
                    
                elif self.is_connected:
                    # Already connected, just check if server is still running
                    if not self._is_server_running():
                        logger.warning("Server stopped unexpectedly, restarting...")
                        self._start_server()
            else:
                logger.warning(f"Interface {self.interface} has IP {current_ip} but no internet connectivity")
                if self.is_connected:
                    self.is_connected = False
                    self._stop_server()
        else:
            if self.is_connected:
                logger.info(f"Network disconnected from {self.interface}")
                self.is_connected = False
                self.last_ip = None
                self._stop_server()
    
    def run(self):
        """
        Main monitoring loop
        """
        logger.info(f"Starting network monitor for interface: {self.interface}")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info(f"Server script: {self.script_path}")
        
        while self.running:
            try:
                self.check_connection()
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)
        
        # Clean up
        self._stop_server()
        logger.info("Network monitor stopped")

def main():
    """
    Main function to run the network monitor
    """
    # Configuration
    INTERFACE = 'wlan0'
    CHECK_INTERVAL = 5  # seconds
    SCRIPT_PATH = './start_server.sh'
    
    # Check if script exists
    if not os.path.exists(SCRIPT_PATH):
        logger.error(f"Server script not found: {SCRIPT_PATH}")
        sys.exit(1)
    
    # Create and run monitor
    monitor = NetworkMonitor(
        interface=INTERFACE,
        check_interval=CHECK_INTERVAL,
        script_path=SCRIPT_PATH
    )
    
    try:
        monitor.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
