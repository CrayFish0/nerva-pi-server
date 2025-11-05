import RPi.GPIO as GPIO
import time

print("Sensor Monitor Initialized")
# GPIO Setup
GPIO.setmode(GPIO.BCM)

# Pin Definitions
TRIG = 23
ECHO = 24
TURBIDITY_D0 = 17

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(TURBIDITY_D0, GPIO.IN)

# Get CPU Temperature
def get_cpu_temp():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp = int(f.read()) / 1000
    return round(temp, 2)

# Get Ultrasonic Distance
def get_distance():
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
    if GPIO.input(TURBIDITY_D0) == GPIO.HIGH:
        return "Clear"
    else:
        return "Turbid"

try:
    while True:
        temp = get_cpu_temp()
        distance = get_distance()
        turbidity_status = get_turbidity()

        print(f"Temperature: {(int)(temp - 15.5)} °C \t|\t Distance: {distance} cm \t|\t Water: {turbidity_status}")
        time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()
