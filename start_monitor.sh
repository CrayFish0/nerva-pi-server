#!/bin/bash
# Startup script for the network monitor

# Navigate to the project directory
cd /home/user/projects/stats-boradcaster

# Activate the virtual environment
source venv/bin/activate

# Run the network monitor
python3 network_monitor.py
