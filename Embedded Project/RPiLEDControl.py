import time
import RPi.GPIO as GPIO

# GPIO pin setup for Traffic Light 1
RED_LED_PIN_1 = 17    # GPIO pin for red light of Traffic Light 1
ORANGE_LED_PIN_1 = 27 # GPIO pin for orange light of Traffic Light 1
GREEN_LED_PIN_1 = 22   # GPIO pin for green light of Traffic Light 1

# GPIO pin setup for Traffic Light 2
RED_LED_PIN_2 = 18    # GPIO pin for red light of Traffic Light 2
ORANGE_LED_PIN_2 = 23 # GPIO pin for orange light of Traffic Light 2
GREEN_LED_PIN_2 = 25   # GPIO pin for green light of Traffic Light 2

# Setup GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
# Initialize GPIO for Traffic Light 1
GPIO.setup(RED_LED_PIN_1, GPIO.OUT)
GPIO.setup(ORANGE_LED_PIN_1, GPIO.OUT)
GPIO.setup(GREEN_LED_PIN_1, GPIO.OUT)

# Initialize GPIO for Traffic Light 2
GPIO.setup(RED_LED_PIN_2, GPIO.OUT)
GPIO.setup(ORANGE_LED_PIN_2, GPIO.OUT)
GPIO.setup(GREEN_LED_PIN_2, GPIO.OUT)

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

# Function to change traffic light states and update GPIO
def change_light(light_number, state):
    print(f"Traffic Light {light_number} is now {state}")
    if light_number == 1:  # Update GPIO for Traffic Light 1
        if state == RED:
            GPIO.output(RED_LED_PIN_1, GPIO.HIGH)
            GPIO.output(ORANGE_LED_PIN_1, GPIO.LOW)
            GPIO.output(GREEN_LED_PIN_1, GPIO.LOW)
        elif state == ORANGE:
            GPIO.output(RED_LED_PIN_1, GPIO.LOW)
            GPIO.output(ORANGE_LED_PIN_1, GPIO.HIGH)
            GPIO.output(GREEN_LED_PIN_1, GPIO.LOW)
        elif state == GREEN:
            GPIO.output(RED_LED_PIN_1, GPIO.LOW)
            GPIO.output(ORANGE_LED_PIN_1, GPIO.LOW)
            GPIO.output(GREEN_LED_PIN_1, GPIO.HIGH)

    elif light_number == 2:  # Update GPIO for Traffic Light 2
        if state == RED:
            GPIO.output(RED_LED_PIN_2, GPIO.HIGH)
            GPIO.output(ORANGE_LED_PIN_2, GPIO.LOW)
            GPIO.output(GREEN_LED_PIN_2, GPIO.LOW)
        elif state == ORANGE:
            GPIO.output(RED_LED_PIN_2, GPIO.LOW)
            GPIO.output(ORANGE_LED_PIN_2, GPIO.HIGH)
            GPIO.output(GREEN_LED_PIN_2, GPIO.LOW)
        elif state == GREEN:
            GPIO.output(RED_LED_PIN_2, GPIO.LOW)
            GPIO.output(ORANGE_LED_PIN_2, GPIO.LOW)
            GPIO.output(GREEN_LED_PIN_2, GPIO.HIGH)

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

# Set the initial state to RED for both Traffic Lights
change_light(1, RED)
change_light(2, RED)

time.sleep(1)  # Wait 1 second before starting the main loop

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
        #green_time = 0

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

            # Print the vehicle count during green light
            print(f"Vehicle Count Cam 1 (during green): {vehicle_count_cam1}")
            print(f"Vehicle Count Cam 2 (during green): {vehicle_count_cam2}")

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
            else:
                # If the green time has not reached the minimum, allow a break to check the next loop
                break  # Exit the while loop temporarily to check the next state

        # Green light logic for Traffic Light 2
        while traffic_light_2_state == GREEN:
            time.sleep(1)
            green_time += 1

            # Print the vehicle count during green light
            print(f"Vehicle Count Cam 1 (during green): {vehicle_count_cam1}")
            print(f"Vehicle Count Cam 2 (during green): {vehicle_count_cam2}")

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
            else:
                # If the green time has not reached the minimum, allow a break to check the next loop
                break  # Exit the while loop temporarily to check the next state

        # Print the current state of traffic lights
        print(f"Traffic Light 1: {traffic_light_1_state}, \nTraffic Light 2: {traffic_light_2_state}")

        # Wait for a moment before the next cycle
        time.sleep(DELAY_BETWEEN_CYCLES)

except KeyboardInterrupt:
    print("Traffic control program interrupted.")

finally:
    # Turn off all LEDs when the program ends
    GPIO.output(RED_LED_PIN_1, GPIO.LOW)
    GPIO.output(ORANGE_LED_PIN_1, GPIO.LOW)
    GPIO.output(GREEN_LED_PIN_1, GPIO.LOW)
    GPIO.output(RED_LED_PIN_2, GPIO.LOW)
    GPIO.output(ORANGE_LED_PIN_2, GPIO.LOW)
    GPIO.output(GREEN_LED_PIN_2, GPIO.LOW)
    GPIO.cleanup()  # Clean up GPIO settings
