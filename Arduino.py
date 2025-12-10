#!/usr/bin/env python3
import serial
import json
import time

# ==============================
# SERIAL CONNECTION (USB ARDUINO)
# ==============================
# Change to /dev/ttyUSB0 if required
arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

ph_value = None
turbidity_value = None

# ==============================
# READ SENSOR DATA FUNCTION
# ==============================
def read_arduino_sensors():
    global ph_value, turbidity_value
    try:
        line = arduino.readline().decode().strip()
        if line.startswith("{") and line.endswith("}"):
            data = json.loads(line)

            ph_value = float(data.get("ph"))
            turbidity_value = float(data.get("turbidity"))
            return True
    except:
        pass
    return False


# ==============================
# MAIN LOOP
# ==============================
print("\n📡 Reading from Arduino... (Press CTRL+C to stop)\n")

while True:
    if read_arduino_sensors():
        print(f"pH: {ph_value:.2f} | Turbidity: {turbidity_value:.2f}")
    else:
        print("Waiting for data...")

    time.sleep(1)
