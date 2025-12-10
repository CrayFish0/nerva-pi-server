import RPi.GPIO as GPIO
import time

# Pin Definitions
TRIG = 23
ECHO = 24
TURBIDITY_D0 = 17

# GPIO Setup with error handling
GPIO_INITIALIZED = False
try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.setup(TURBIDITY_D0, GPIO.IN)
    GPIO_INITIALIZED = True
except (RuntimeError, Exception) as e:
    print(f"Warning: GPIO initialization failed: {e}")
    print("Sensors will return simulated data.")

# Get CPU Temperature
def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000
        return round(temp - 15.5, 2)
    except:
        # Simulated temperature if file not available
        import random
        return round(25.0 + random.uniform(-2.0, 2.0), 2)

# Get Ultrasonic Distance
def get_distance():
    if not GPIO_INITIALIZED:
        # Return simulated distance
        import random
        return round(25.0 + random.uniform(-2.0, 2.0), 2)
    
    GPIO.output(TRIG, False)
    time.sleep(0.05)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    return round(distance, 2)

# Get Turbidity Status
def get_turbidity():
    if not GPIO_INITIALIZED:
        # Return simulated turbidity
        import random
        return "Clear" if random.random() > 0.2 else "Turbid"
    
    if GPIO.input(TURBIDITY_D0) == GPIO.HIGH:
        return "Clear"
    else:
        return "Turbid"

# Main function to return all values at once
def read_all_sensors():
    try:
        return {
            "temperature_c": get_cpu_temp(),
            "distance_cm": get_distance(),
            "turbidity": get_turbidity()
        }
    except Exception as e:
        return {"error": str(e)}

# Cleanup function (call only on exit)
def cleanup_gpio():
    if GPIO_INITIALIZED:
        GPIO.cleanup()


print(read_all_sensors())