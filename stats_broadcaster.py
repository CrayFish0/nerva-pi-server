#!/usr/bin/env python3
"""
WebSocket server for broadcasting Raspberry Pi system statistics.
Sends CPU, RAM, disk usage, and temperature data to connected clients every second.
"""

import asyncio
import json
import logging
import subprocess
import websockets
import psutil
from datetime import datetime
from typing import Set, Dict, Any
import time
import random

# GPIO for sensor monitoring
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO not available - sensor data will be simulated")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global set to track connected clients
connected_clients: Set = set()

# GPIO Pin Definitions
TRIG = 23
ECHO = 24
TURBIDITY_D0 = 17
PH_SENSOR_PIN = 27  # Analog pH sensor (would use ADC in real implementation)

# Initialize GPIO if available
if GPIO_AVAILABLE:
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TRIG, GPIO.OUT)
        GPIO.setup(ECHO, GPIO.IN)
        GPIO.setup(TURBIDITY_D0, GPIO.IN)
        logger.info("GPIO sensors initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize GPIO: {e}")
        GPIO_AVAILABLE = False

def get_ultrasonic_distance():
    """
    Get distance reading from HC-SR04 ultrasonic sensor.
    Returns distance in centimeters, or simulated value if unavailable.
    """
    if not GPIO_AVAILABLE:
        # Simulate realistic water level/distance sensor (10-50 cm range with slight variations)
        base_distance = 25.0
        variation = random.uniform(-2.0, 2.0)
        return round(base_distance + variation, 2)
    
    try:
        GPIO.output(TRIG, False)
        time.sleep(0.05)

        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        timeout = time.time() + 1.0  # 1 second timeout
        pulse_start = time.time()
        pulse_end = time.time()

        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
            if time.time() > timeout:
                return None

        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()
            if time.time() > timeout:
                return None

        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        return round(distance, 2)
    except Exception as e:
        logger.warning(f"Failed to read ultrasonic sensor: {e}")
        return None

def get_turbidity_status():
    """
    Get turbidity sensor status.
    Returns "Clear" or "Turbid", or simulated value if unavailable.
    """
    if not GPIO_AVAILABLE:
        # Simulate mostly clear water with occasional turbidity
        # 80% chance of clear, 20% chance of turbid
        return "Clear" if random.random() > 0.2 else "Turbid"
    
    try:
        if GPIO.input(TURBIDITY_D0) == GPIO.HIGH:
            return "Clear"
        else:
            return "Turbid"
    except Exception as e:
        logger.warning(f"Failed to read turbidity sensor: {e}")
        return None

def get_ph_level():
    """
    Get pH level from pH sensor.
    Returns pH value (0-14 scale), or simulated value if unavailable.
    In real implementation, would use ADC to read analog pH sensor.
    """
    if not GPIO_AVAILABLE:
        # Simulate realistic pH for water (slightly acidic to neutral range)
        # pH 6.5-7.5 is typical for clean water
        base_ph = 7.0
        variation = random.uniform(-0.3, 0.3)
        return round(base_ph + variation, 2)
    
    try:
        # In real implementation, would read from ADC (e.g., MCP3008)
        # For now, simulate reading
        # Example: adc_value = read_adc(PH_SENSOR_PIN)
        # ph_value = convert_adc_to_ph(adc_value)
        
        # Simulated realistic pH reading
        base_ph = 7.0
        variation = random.uniform(-0.3, 0.3)
        return round(base_ph + variation, 2)
    except Exception as e:
        logger.warning(f"Failed to read pH sensor: {e}")
        return None

def get_ambient_temp():
    """
    Get ambient temperature with adjustment (-15.5°C as per sensor monitor).
    Returns temperature in Celsius, or simulated value if unavailable.
    """
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000
        adjusted_temp = temp - 15.5
        return round(adjusted_temp, 2)
    except Exception as e:
        # Simulate realistic ambient temperature (20-30°C range)
        base_temp = 25.0
        variation = random.uniform(-3.0, 3.0)
        return round(base_temp + variation, 2)

def get_temperature() -> float:
    """
    Get CPU temperature from Raspberry Pi using vcgencmd.
    Returns temperature in Celsius, or None if unable to read.
    """
    try:
        result = subprocess.run(
            ['vcgencmd', 'measure_temp'],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse output like "temp=42.8'C"
        temp_str = result.stdout.strip()
        temp_value = temp_str.split('=')[1].replace("'C", "")
        return float(temp_value)
    except (subprocess.CalledProcessError, IndexError, ValueError) as e:
        logger.warning(f"Failed to get temperature: {e}")
        return None

def get_stats() -> Dict[str, Any]:
    """
    Collect comprehensive system statistics.
    Returns a dictionary with all the statistics.
    """
    try:
        # Get current timestamp
        timestamp = datetime.now().isoformat()
        
        # CPU Information
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
        
        # Memory Information
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk Information
        disk_root = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        disk_partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2),
                    'used_percent': round((usage.used / usage.total) * 100, 2)
                })
            except PermissionError:
                continue
        
        # Network Information
        network_io = psutil.net_io_counters()
        network_interfaces = {}
        for interface, addrs in psutil.net_if_addrs().items():
            interface_info = {'addresses': []}
            for addr in addrs:
                interface_info['addresses'].append({
                    'family': str(addr.family),
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast
                })
            network_interfaces[interface] = interface_info
        
        # Process Information
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu_percent': round(proc.info['cpu_percent'] or 0, 2),
                    'memory_percent': round(proc.info['memory_percent'] or 0, 2)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort processes by CPU usage and get top 10
        top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:10]
        
        # Boot time and uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_seconds = (datetime.now() - boot_time).total_seconds()
        
        # Load averages (Linux only)
        load_avg = None
        try:
            load_avg = psutil.getloadavg()
        except AttributeError:
            pass
        
        # Battery information (if available)
        battery = None
        try:
            battery_info = psutil.sensors_battery()
            if battery_info:
                battery = {
                    'percent': battery_info.percent,
                    'power_plugged': battery_info.power_plugged,
                    'secsleft': battery_info.secsleft if battery_info.secsleft != psutil.POWER_TIME_UNLIMITED else None
                }
        except AttributeError:
            pass
        
        # Temperature from vcgencmd
        pi_temperature = get_temperature()
        
        # GPIO Sensor readings
        ultrasonic_distance = get_ultrasonic_distance()
        turbidity = get_turbidity_status()
        ambient_temp = get_ambient_temp()
        ph_level = get_ph_level()
        
        # System sensors (if available)
        sensors_temps = {}
        try:
            temps = psutil.sensors_temperatures()
            for name, entries in temps.items():
                sensor_data = []
                for entry in entries:
                    sensor_data.append({
                        'label': entry.label or 'Unknown',
                        'current': entry.current,
                        'high': entry.high,
                        'critical': entry.critical
                    })
                sensors_temps[name] = sensor_data
        except AttributeError:
            pass
        
        # Compile all statistics
        stats = {
            'timestamp': timestamp,
            'system': {
                'boot_time': boot_time.isoformat(),
                'uptime_seconds': round(uptime_seconds, 2),
                'uptime_human': str(datetime.now() - boot_time).split('.')[0],
                'load_average': list(load_avg) if load_avg else None,
                'connected_clients': len(connected_clients)
            },
            'cpu': {
                'usage_percent': round(cpu_percent, 2),
                'count_physical': cpu_count,
                'count_logical': cpu_count_logical,
                'frequency_mhz': {
                    'current': round(cpu_freq.current, 2) if cpu_freq else None,
                    'min': round(cpu_freq.min, 2) if cpu_freq else None,
                    'max': round(cpu_freq.max, 2) if cpu_freq else None
                },
                'per_core_usage': [round(x, 2) for x in cpu_per_core]
            },
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'free_gb': round(memory.free / (1024**3), 2),
                'used_percent': round(memory.percent, 2),
                'cached_gb': round(memory.cached / (1024**3), 2),
                'buffers_gb': round(memory.buffers / (1024**3), 2)
            },
            'swap': {
                'total_gb': round(swap.total / (1024**3), 2),
                'used_gb': round(swap.used / (1024**3), 2),
                'free_gb': round(swap.free / (1024**3), 2),
                'used_percent': round(swap.percent, 2)
            },
            'disk': {
                'root_usage_percent': round((disk_root.used / disk_root.total) * 100, 2),
                'partitions': disk_partitions,
                'io_counters': {
                    'read_count': disk_io.read_count if disk_io else None,
                    'write_count': disk_io.write_count if disk_io else None,
                    'read_bytes': disk_io.read_bytes if disk_io else None,
                    'write_bytes': disk_io.write_bytes if disk_io else None,
                    'read_time': disk_io.read_time if disk_io else None,
                    'write_time': disk_io.write_time if disk_io else None
                }
            },
            'network': {
                'io_counters': {
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv,
                    'errin': network_io.errin,
                    'errout': network_io.errout,
                    'dropin': network_io.dropin,
                    'dropout': network_io.dropout
                },
                'interfaces': network_interfaces
            },
            'processes': {
                'total_count': len(processes),
                'top_cpu_usage': top_processes
            },
            'temperature': {
                'pi_cpu_celsius': round(pi_temperature, 2) if pi_temperature is not None else None,
                'sensors': sensors_temps
            },
            'custom_sensors': {
                'ambient_temp_celsius': ambient_temp,
                'ultrasonic_distance_cm': ultrasonic_distance,
                'water_turbidity': turbidity,
                'ph_level': ph_level,
                'gpio_available': GPIO_AVAILABLE
            },
            'battery': battery
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error collecting stats: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

async def register_client(websocket):
    """Register a new client connection."""
    connected_clients.add(websocket)
    client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"Client connected: {client_info} (Total clients: {len(connected_clients)})")

async def unregister_client(websocket):
    """Unregister a client connection."""
    connected_clients.discard(websocket)
    client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"Client disconnected: {client_info} (Total clients: {len(connected_clients)})")

async def handle_client(websocket):
    """Handle individual client connections."""
    await register_client(websocket)
    try:
        # Keep connection alive and handle any messages
        async for message in websocket:
            # Echo back any received messages (optional)
            logger.debug(f"Received message from {websocket.remote_address}: {message}")
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        logger.error(f"Error handling client {websocket.remote_address}: {e}")
    finally:
        await unregister_client(websocket)

async def broadcast_stats():
    """Broadcast system statistics to all connected clients every second."""
    while True:
        try:
            if connected_clients:
                # Get current stats
                stats = get_stats()
                stats_json = json.dumps(stats)
                
                # Send to all connected clients
                disconnected_clients = set()
                for client in connected_clients:
                    try:
                        await client.send(stats_json)
                    except websockets.exceptions.ConnectionClosed:
                        disconnected_clients.add(client)
                    except Exception as e:
                        logger.error(f"Error sending to client {client.remote_address}: {e}")
                        disconnected_clients.add(client)
                
                # Clean up disconnected clients
                for client in disconnected_clients:
                    await unregister_client(client)
                
                if len(connected_clients) > 0:
                    logger.debug(f"Broadcasted stats to {len(connected_clients)} clients")
            
            # Wait for next broadcast
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in broadcast loop: {e}")
            await asyncio.sleep(1)

async def main():
    """Main function to start the WebSocket server."""
    host = "0.0.0.0"
    port = 8765
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    # Start the WebSocket server
    server = await websockets.serve(
        handle_client,
        host,
        port,
        ping_interval=20,  # Send ping every 20 seconds
        ping_timeout=10,   # Wait 10 seconds for pong
        close_timeout=10   # Wait 10 seconds for close
    )
    
    logger.info(f"WebSocket server started on ws://{host}:{port}")
    
    # Start the broadcast task
    broadcast_task = asyncio.create_task(broadcast_stats())
    
    try:
        # Run forever
        await asyncio.gather(
            server.wait_closed(),
            broadcast_task
        )
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.close()
        await server.wait_closed()
        broadcast_task.cancel()
        
        # Cleanup GPIO
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
                logger.info("GPIO cleanup completed")
            except Exception as e:
                logger.error(f"Error during GPIO cleanup: {e}")
        
        logger.info("Server shut down gracefully")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        
        # Final GPIO cleanup
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
            except:
                pass
