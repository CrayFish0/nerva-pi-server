#!/bin/bash
# Boot Service Setup Summary for Raspberry Pi Stats Broadcaster

echo "========================================"
echo "🥧 Raspberry Pi Stats Broadcaster"
echo "   Automated Boot Service Setup"
echo "========================================"
echo ""

# Check if service exists
if systemctl list-unit-files | grep -q network-monitor.service; then
    echo "✅ Service Status: INSTALLED"
    
    # Check if enabled
    if systemctl is-enabled network-monitor.service >/dev/null 2>&1; then
        echo "✅ Auto-Start: ENABLED"
    else
        echo "❌ Auto-Start: DISABLED"
    fi
    
    # Check if running
    if systemctl is-active network-monitor.service >/dev/null 2>&1; then
        echo "✅ Currently: RUNNING"
        
        # Get IP address
        IP=$(ip addr show wlan0 | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d'/' -f1)
        if [ ! -z "$IP" ]; then
            echo "✅ Network: CONNECTED ($IP)"
        else
            echo "⚠️  Network: CHECKING..."
        fi
        
        # Check if stats server is running
        if pgrep -f stats_broadcaster.py >/dev/null 2>&1; then
            echo "✅ Stats Server: RUNNING"
        else
            echo "⚠️  Stats Server: STARTING..."
        fi
        
    else
        echo "❌ Currently: STOPPED"
    fi
else
    echo "❌ Service Status: NOT INSTALLED"
fi

echo ""
echo "🔧 Management Commands:"
echo "   ./service_manager.sh status    # Check status"
echo "   ./service_manager.sh logs      # View logs"
echo "   ./service_manager.sh restart   # Restart"
echo ""
echo "🌐 Access Dashboard:"
echo "   Open client.html in browser"
echo "   WebSocket: ws://localhost:8765"
echo ""
echo "📋 What happens on boot:"
echo "   1. System boots → Service starts automatically"
echo "   2. Monitors wlan0 → Detects network connection"
echo "   3. Network found → Starts stats broadcaster"
echo "   4. Dashboard available → Real-time monitoring"
echo ""
echo "🚀 Your Raspberry Pi is now fully automated!"
echo "========================================"
