# Raspberry Pi Stats Broadcaster

A WebSocket server that broadcasts real-time system statistics from a Raspberry Pi to connected clients.

## Features

- **Comprehensive real-time monitoring**: Sends detailed system stats every second
- **WebSocket communication**: Efficient bi-directional communication
- **Multiple clients**: Supports multiple simultaneous connections
- **Extensive system information**: 
  - CPU usage (overall + per-core breakdown)
  - Memory usage (RAM + swap with detailed breakdowns)
  - Storage usage (all partitions + I/O statistics)
  - Network statistics (I/O counters + interface details)
  - Process information (top CPU consumers)
  - Temperature monitoring (Pi CPU + all sensors)
  - System information (uptime, load averages, boot time)
  - Battery information (if available)
- **Beautiful web interface**: Modern, responsive dashboard
- **Graceful handling**: Proper connection management and error handling
- **Detailed logging**: Comprehensive logging for monitoring and debugging
- **Mobile responsive**: Works on desktop, tablet, and mobile devices

## System Requirements

- Raspberry Pi (any model)
- Python 3.7+
- Internet connection for installing dependencies

## Installation

1. Clone or download this project to your Raspberry Pi
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Server

Run the server with:
```bash
python3 stats_broadcaster.py
```

The server will start on `0.0.0.0:8765` and begin broadcasting stats to any connected clients.

### Testing the Server

1. Open `client.html` in a web browser
2. Make sure to update the WebSocket URL in the HTML file to point to your Raspberry Pi's IP address
3. The page will show real-time system statistics

### Connecting from Other Applications

Connect to the WebSocket server at `ws://YOUR_PI_IP:8765`

The server sends JSON data in this format:
```json
{
    "timestamp": "2025-07-14T10:30:00.123456",
    "cpu_usage_percent": 45.2,
    "ram_usage_percent": 62.8,
    "disk_usage_percent": 78.5,
    "temperature_celsius": 42.8,
    "connected_clients": 3
}
```

## System Stats Collected

### Comprehensive System Information:
- **System Overview**: Boot time, uptime, load averages, connected clients
- **CPU Information**: 
  - Overall usage percentage
  - Physical and logical core counts
  - CPU frequency (current, min, max)
  - Per-core usage breakdown
- **Memory Information**:
  - RAM usage (total, used, available, cached, buffers)
  - Swap usage and statistics
- **Storage Information**:
  - Root partition usage
  - All mounted partitions with detailed stats
  - Disk I/O counters (read/write operations and bytes)
- **Network Information**:
  - Network I/O counters (bytes sent/received, packets, errors, dropped)
  - All network interfaces with IP addresses
- **Process Information**:
  - Total process count
  - Top 10 processes by CPU usage
  - Process details (PID, name, CPU%, memory%)
- **Temperature Information**:
  - Raspberry Pi CPU temperature (via `vcgencmd`)
  - All available system sensors
- **Battery Information** (if available):
  - Battery level percentage
  - Power adapter connection status
  - Time remaining estimate

### Data Format
The server now sends comprehensive JSON data in this structure:
```json
{
    "timestamp": "2025-07-14T10:30:00.123456",
    "system": {
        "boot_time": "2025-07-14T08:00:00.000000",
        "uptime_seconds": 9000.45,
        "uptime_human": "2:30:00",
        "load_average": [0.15, 0.25, 0.35],
        "connected_clients": 2
    },
    "cpu": {
        "usage_percent": 45.2,
        "count_physical": 4,
        "count_logical": 4,
        "frequency_mhz": {
            "current": 1400.0,
            "min": 600.0,
            "max": 1400.0
        },
        "per_core_usage": [42.1, 48.3, 44.7, 45.9]
    },
    "memory": {
        "total_gb": 8.0,
        "available_gb": 4.2,
        "used_gb": 3.8,
        "free_gb": 0.5,
        "used_percent": 47.5,
        "cached_gb": 2.1,
        "buffers_gb": 0.3
    },
    "swap": {
        "total_gb": 2.0,
        "used_gb": 0.1,
        "free_gb": 1.9,
        "used_percent": 5.0
    },
    "disk": {
        "root_usage_percent": 78.5,
        "partitions": [...],
        "io_counters": {
            "read_count": 12345,
            "write_count": 6789,
            "read_bytes": 1234567890,
            "write_bytes": 987654321
        }
    },
    "network": {
        "io_counters": {
            "bytes_sent": 1234567890,
            "bytes_recv": 9876543210,
            "packets_sent": 123456,
            "packets_recv": 654321
        },
        "interfaces": {...}
    },
    "processes": {
        "total_count": 156,
        "top_cpu_usage": [...]
    },
    "temperature": {
        "pi_cpu_celsius": 42.8,
        "sensors": {...}
    },
    "battery": {
        "percent": 85.0,
        "power_plugged": true,
        "secsleft": 3600
    }
}
```

## Configuration

You can modify the following settings in `stats_broadcaster.py`:

- **Host**: Change `host = "0.0.0.0"` to bind to a specific interface
- **Port**: Change `port = 8765` to use a different port
- **Broadcast interval**: Change `await asyncio.sleep(1)` to modify update frequency
- **Ping settings**: Adjust `ping_interval` and `ping_timeout` for connection management

## Running as a Service

To run the server automatically on boot, create a systemd service:

1. Create the service file:
   ```bash
   sudo nano /etc/systemd/system/stats-broadcaster.service
   ```

2. Add the following content:
   ```ini
   [Unit]
   Description=Raspberry Pi Stats Broadcaster
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/projects/stats-broadcaster
   ExecStart=/usr/bin/python3 /home/pi/projects/stats-broadcaster/stats_broadcaster.py
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable stats-broadcaster.service
   sudo systemctl start stats-broadcaster.service
   ```

4. Check the service status:
   ```bash
   sudo systemctl status stats-broadcaster.service
   ```

## Troubleshooting

### Temperature Reading Issues
If temperature reading fails, ensure:
- You're running on a Raspberry Pi
- `vcgencmd` is available in the system PATH
- The user has permission to execute `vcgencmd`

### Connection Issues
- Check that port 8765 is not blocked by a firewall
- Verify the server is binding to the correct interface
- Check the logs for connection errors

### Performance
- The server is designed to be lightweight and efficient
- Monitor CPU usage if you have many connected clients
- Consider adjusting the broadcast interval for better performance

## Logs

The server outputs detailed logs including:
- Client connections and disconnections
- Error messages
- Debug information (when enabled)

## Dependencies

- `websockets`: WebSocket server implementation
- `psutil`: System and process utilities
- `asyncio`: Asynchronous I/O (built-in)
- `json`: JSON handling (built-in)
- `subprocess`: For executing system commands (built-in)

## License

This project is open source and available under the MIT License.

## Project Files

```
stats-boradcaster/
├── stats_broadcaster.py      # Main WebSocket server with comprehensive system monitoring
├── network_monitor.py        # Network monitoring script with automatic server management
├── client.html              # Advanced web dashboard for viewing system stats
├── start_server.sh          # Script to start the stats broadcaster server
├── start_monitor.sh         # Script to start the network monitor
├── service_manager.sh       # Service management script for easy control
├── test_network.py          # Test script for network detection functionality
├── network-monitor.service  # Systemd service file for automatic startup
├── requirements.txt         # Python dependencies
├── README.md               # This documentation
├── network_monitor.log     # Network monitor log file
└── venv/                   # Python virtual environment
```

## Quick Start

1. **Install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Test network detection:**
   ```bash
   python3 test_network.py
   ```

3. **Start network monitor (recommended):**
   ```bash
   ./start_monitor.sh
   ```

4. **Or start server manually:**
   ```bash
   ./start_server.sh
   ```

5. **View dashboard:**
   - Open `client.html` in a web browser
   - Update the WebSocket URL to your Pi's IP address
   - Enjoy real-time system monitoring!

## Features Summary

✅ **Comprehensive System Monitoring**
- CPU, Memory, Storage, Network, Processes, Temperature
- Real-time WebSocket updates every second
- Beautiful, responsive web interface

✅ **Automatic Network Management**
- Monitors wlan0 interface for connectivity
- Automatically starts/stops server based on network status
- Robust detection with multiple fallback methods

✅ **Production Ready**
- Systemd service for automatic startup
- Comprehensive logging and error handling
- Graceful shutdown and restart capabilities

✅ **Easy Deployment**
- Simple installation and setup
- Works on any Raspberry Pi with Python 3.7+
- Mobile-responsive web interface

## ✅ Automated Boot Service Setup Complete

Your Raspberry Pi is now configured with an automated network monitoring service that:

### Current Setup Status:
- ✅ **Service Installed**: `network-monitor.service` installed in systemd
- ✅ **Auto-Start Enabled**: Service will start automatically on boot
- ✅ **Currently Running**: Network monitor is actively monitoring wlan0
- ✅ **Server Management**: Stats broadcaster automatically managed based on network status

### Service Management Commands:

**Quick Management (using service_manager.sh):**
```bash
./service_manager.sh status    # Check service status
./service_manager.sh logs      # View live logs
./service_manager.sh restart   # Restart service
./service_manager.sh stop      # Stop service
./service_manager.sh start     # Start service
```

**Manual systemctl Commands:**
```bash
sudo systemctl status network-monitor.service     # Check status
sudo systemctl restart network-monitor.service    # Restart
sudo systemctl stop network-monitor.service       # Stop
sudo systemctl start network-monitor.service      # Start
sudo journalctl -u network-monitor.service -f     # View logs
```

### What Happens on Boot:
1. **System Boots** → Network monitor service starts automatically
2. **Network Detection** → Monitors wlan0 for connectivity every 5 seconds
3. **Connection Found** → Automatically starts stats broadcaster server
4. **Network Lost** → Automatically stops server to save resources
5. **Reconnection** → Automatically restarts server

### Service Files:
- **Main Service**: `/etc/systemd/system/network-monitor.service`
- **Management Script**: `./service_manager.sh`
- **Log File**: `./network_monitor.log`
- **System Logs**: `journalctl -u network-monitor.service`

### Current Status:
```
● network-monitor.service - Network Monitor for Raspberry Pi Stats Broadcaster
   Loaded: loaded (/etc/systemd/system/network-monitor.service; enabled; preset: enabled)
   Active: active (running)
   
Network: Connected (192.168.29.112)
Stats Server: Running (automatically managed)
```

Your Raspberry Pi will now automatically start monitoring and broadcasting system statistics whenever it connects to a network, with no manual intervention required! 🚀
