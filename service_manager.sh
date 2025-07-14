#!/bin/bash
# Service management script for Network Monitor

SERVICE_NAME="network-monitor.service"

case "$1" in
    start)
        echo "Starting network monitor service..."
        sudo systemctl start $SERVICE_NAME
        ;;
    stop)
        echo "Stopping network monitor service..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "Restarting network monitor service..."
        sudo systemctl restart $SERVICE_NAME
        ;;
    status)
        sudo systemctl status $SERVICE_NAME
        ;;
    enable)
        echo "Enabling network monitor service for boot..."
        sudo systemctl enable $SERVICE_NAME
        ;;
    disable)
        echo "Disabling network monitor service from boot..."
        sudo systemctl disable $SERVICE_NAME
        ;;
    logs)
        echo "Showing recent logs (press Ctrl+C to exit)..."
        sudo journalctl -u $SERVICE_NAME -f --lines=50
        ;;
    install)
        echo "Installing network monitor service..."
        sudo cp network-monitor.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable $SERVICE_NAME
        sudo systemctl start $SERVICE_NAME
        echo "Service installed and started!"
        ;;
    uninstall)
        echo "Uninstalling network monitor service..."
        sudo systemctl stop $SERVICE_NAME
        sudo systemctl disable $SERVICE_NAME
        sudo rm /etc/systemd/system/$SERVICE_NAME
        sudo systemctl daemon-reload
        echo "Service uninstalled!"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|enable|disable|logs|install|uninstall}"
        echo ""
        echo "Commands:"
        echo "  start     - Start the service"
        echo "  stop      - Stop the service"
        echo "  restart   - Restart the service"
        echo "  status    - Show service status"
        echo "  enable    - Enable service for boot"
        echo "  disable   - Disable service from boot"
        echo "  logs      - Show live service logs"
        echo "  install   - Install and enable the service"
        echo "  uninstall - Remove the service completely"
        exit 1
        ;;
esac
