#!/bin/bash
# Startup script for the stats broadcaster server

# Navigate to the project directory
cd /home/user/projects/stats-boradcaster

# Activate the virtual environment
source venv/bin/activate

# Run the server
python3 stats_broadcaster.py
