import RPi.GPIO as GPIO
import time

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)  # Green LED
GPIO.setup(23, GPIO.OUT)  # Orange LED
GPIO.setup(25, GPIO.OUT)  # Red LED

# Traffic light state constants
RED = "RED"
GREEN = "GREEN"
ORANGE = "ORANGE"

# Time delays in seconds for the light states
DELAY_GREEN_MIN = 5  # Minimum time the light stays green
DELAY_ORANGE = 3  # Time the light stays orange before turning red
DELAY_RED = 2  # Time the light stays red after turning from green
DELAY_BETWEEN_CYCLES = 2  # Delay between each cycle of checking

# Initialize traffic light state for both sets of lights
traffic_light_1_state = RED
traffic_light_2_state = RED

# Initialize counters for vehicle count simulation
camera_1_counter = 0
camera_1_cycle = 0

camera_2_counter = 0
camera_2_cycle = 0

green_time = 0

# Function to change traffic light states and control LEDs for Traffic Light 2
def change_light(light_number, state):
    if light_number == 2:  # Only control LEDs for Traffic Light 2
        if state == GREEN:
            GPIO.output(18, GPIO.HIGH)
            GPIO.output(23, GPIO.LOW)
            GPIO.output(25, GPIO.LOW)
        elif state == ORANGE:
            GPIO.output(18, GPIO.LOW)
            GPIO.output(23, GPIO.HIGH)
            GPIO.output(25, GPIO.LOW)
        elif state == RED:
            GPIO.output(18, GPIO.LOW)
            GPIO.output(23, GPIO.LOW)
            GPIO.output(25, GPIO.HIGH)
    print(f"Traffic Light {light_number} is now {state}")

# Simulate vehicle count for Camera 1
def get_vehicle_count_cam1():
    global camera_1_counter, camera_1_cycle

    if camera_1_cycle < 3:  # First 10 cycles: 2 vehicles
        camera_1_counter = 2
    elif camera_1_cycle < 6:  # Next 10 cycles: 0 vehicles
        camera_1_counter = 0
    elif camera_1_cycle < 9:  # Next 10 cycles: 4 vehicles
        camera_1_counter = 4
    else:  # Reset cycle
        camera_1_cycle = 0

    camera_1_cycle += 1
    return camera_1_counter

# Simulate vehicle count for Camera 2
def get_vehicle_count_cam2():
    global camera_2_counter, camera_2_cycle

    if camera_2_cycle < 3:  # First 10 cycles: 0 vehicles
        camera_2_counter = 0
    elif camera_2_cycle < 6:  # Next 10 cycles: 2 vehicles
        camera_2_counter = 2
    else:  # Reset cycle
        camera_2_cycle = 0

    camera_2_cycle += 1
    return camera_2_counter

# Initialize cycle count
cycle_count = 0

try:
    # Infinite loop to control the traffic lights
    while True:
        cycle_count += 1  # Increment the cycle count

        # Fetch vehicle count for both cameras
        vehicle_count_cam1 = get_vehicle_count_cam1()
        vehicle_count_cam2 = get_vehicle_count_cam2()

        print(f"Cycle: {cycle_count}")
        print(f"Vehicle Count Cam 1: {vehicle_count_cam1}")
        print(f"Vehicle Count Cam 2 (Simulated): {vehicle_count_cam2}")

        # Green light time counter
        green_time = 0

        # Check which traffic light should go green
        if traffic_light_1_state == RED and traffic_light_2_state == RED:
            if vehicle_count_cam1 > vehicle_count_cam2:
                traffic_light_1_state = GREEN
                change_light(1, GREEN)
                print("Traffic Light 1 is green.")
            elif vehicle_count_cam2 > vehicle_count_cam1:
                traffic_light_2_state = GREEN
                change_light(2, GREEN)
                print("Traffic Light 2 is green.")

        # Green light logic for Traffic Light 1
        while traffic_light_1_state == GREEN:
            time.sleep(1)
            green_time += 1

            # Check after at least 5 seconds if vehicles are detected in the opposite camera
            if green_time >= DELAY_GREEN_MIN:
                if vehicle_count_cam2 > 0:  # Check if the opposite camera has vehicles
                    # Switch to orange before turning red
                    traffic_light_1_state = ORANGE
                    change_light(1, ORANGE)
                    time.sleep(DELAY_ORANGE)  # Wait for orange light
                    traffic_light_1_state = RED
                    change_light(1, RED)
                    time.sleep(DELAY_RED)  # Wait for 2 seconds
                    traffic_light_2_state = GREEN
                    change_light(2, GREEN)
                    print("Traffic Light 2 is green.")
                    green_time = 0  # Reset green_time for the next light
                    break

        # Green light logic for Traffic Light 2
        while traffic_light_2_state == GREEN:
            time.sleep(1)
            green_time += 1

            # Check after at least 5 seconds if vehicles are detected in the opposite camera
            if green_time >= DELAY_GREEN_MIN:
                if vehicle_count_cam1 > 0:  # Check if the opposite camera has vehicles
                    # Switch to orange before turning red
                    traffic_light_2_state = ORANGE
                    change_light(2, ORANGE)
                    time.sleep(DELAY_ORANGE)  # Wait for orange light
                    traffic_light_2_state = RED
                    change_light(2, RED)
                    time.sleep(DELAY_RED)  # Wait for 2 seconds
                    traffic_light_1_state = GREEN
                    change_light(1, GREEN)
                    print("Traffic Light 1 is green.")
                    green_time = 0  # Reset green_time for the next light
                    break

        # Print the current state of traffic lights
        print(f"Traffic Light 1: {traffic_light_1_state}, \nTraffic Light 2: {traffic_light_2_state}")

        # Wait for a moment before the next cycle
        time.sleep(DELAY_BETWEEN_CYCLES)

except KeyboardInterrupt:
    # This block will execute when Ctrl+C is pressed
    print("Exiting program...")

finally:
    # Ensure all LEDs are turned off when the program ends
    GPIO.output(18, GPIO.LOW)
    GPIO.output(23, GPIO.LOW)
    GPIO.output(25, GPIO.LOW)
    GPIO.cleanup()
