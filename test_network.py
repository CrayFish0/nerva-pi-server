#!/usr/bin/env python3
"""
Test script to verify network detection functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from network_monitor import NetworkMonitor

def test_network_detection():
    """Test network detection methods"""
    print("Testing Network Detection Methods")
    print("=" * 40)
    
    monitor = NetworkMonitor()
    
    # Test IP detection
    ip = monitor.get_interface_ip()
    print(f"Detected IP on wlan0: {ip}")
    
    # Test internet connectivity
    has_internet = monitor._test_internet_connectivity()
    print(f"Internet connectivity: {has_internet}")
    
    # Test server status
    server_running = monitor._is_server_running()
    print(f"Server running: {server_running}")
    
    # Test IP validation
    test_ips = ['192.168.1.100', '127.0.0.1', '169.254.1.1', '10.0.0.1']
    print(f"\nIP Validation Tests:")
    for test_ip in test_ips:
        is_valid = monitor._is_valid_ip(test_ip)
        print(f"  {test_ip}: {'Valid' if is_valid else 'Invalid'}")
    
    print("\nCurrent network status:")
    if ip and has_internet:
        print(f"✅ Network connected: {ip}")
    elif ip:
        print(f"⚠️  Interface has IP but no internet: {ip}")
    else:
        print("❌ No network connection detected")

if __name__ == "__main__":
    test_network_detection()
