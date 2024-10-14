import time
import RPi.GPIO as GPIO
import pymysql

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
DELAY_GREEN_MIN = 6  # Minimum time the light stays green
DELAY_ORANGE = 3  # Time the light stays orange before turning red
DELAY_RED = 2  # Time the light stays red after turning from green
DELAY_BETWEEN_CYCLES = 2  # Delay between each cycle of checking
DELAY_AFTER_RED = 2  # Delay after turning red before changing the other light

# Database connection
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='username',
        password='password',
        database='practicedb'
    )

# Fetch vehicle count from the database for Camera 1
def get_vehicle_count_cam1():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = "SELECT VehicleCount FROM TrafficCam1 ORDER BY Date DESC, Time DESC LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else 0
    finally:
        connection.close()

# Fetch vehicle count from the database for Camera 2
def get_vehicle_count_cam2():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = "SELECT VehicleCount FROM TrafficCam2 ORDER BY Date DESC, Time DESC LIMIT 1"  # Adjust the table name if necessary
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else 0
    finally:
        connection.close()

# Check the mode of each traffic camera
def check_mode():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query1 = "SELECT Mode FROM TrafficCam1Mode"
            cursor.execute(query1)
            mode1 = cursor.fetchone()
            mode1 = mode1[0] if mode1 else None
            
            query2 = "SELECT Mode FROM TrafficCam2Mode"
            cursor.execute(query2)
            mode2 = cursor.fetchone()
            mode2 = mode2[0] if mode2 else None
            
            return mode1, mode2
    finally:
        connection.close()

# Function to change traffic light states and update GPIO
def change_light(light_number, state):
    print(f"Traffic Light {light_number} is now {state}")
    if light_number == 1:  # Update GPIO for Traffic Light 1
        GPIO.output(RED_LED_PIN_1, state == RED)
        GPIO.output(ORANGE_LED_PIN_1, state == ORANGE)
        GPIO.output(GREEN_LED_PIN_1, state == GREEN)

    elif light_number == 2:  # Update GPIO for Traffic Light 2
        GPIO.output(RED_LED_PIN_2, state == RED)
        GPIO.output(ORANGE_LED_PIN_2, state == ORANGE)
        GPIO.output(GREEN_LED_PIN_2, state == GREEN)
    
    #delete data from the trafficlight tables
    delete_light_mode(light_number)
    
    # Send the light state to the database
    send_light_state_to_db(light_number, state)

def delete_light_mode(light_number):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Delete previous data in the TrafficLight table for the specified light_number
            query = f"DELETE FROM TrafficLight{light_number}"
            cursor.execute(query)
        connection.commit()  # Commit the transaction
    finally:
        connection.close()

# Function to send the current light state to the database
def send_light_state_to_db(light_number, state):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = f"INSERT INTO TrafficLight{light_number} (Colour) VALUES (%s)"
            cursor.execute(query, (state,))  # Correctly execute the query with the state parameter
        connection.commit()
    finally:
        connection.close()

# Set both traffic lights to RED initially
change_light(1, RED)
change_light(2, RED)

last_green_light = None  # To track the last green light
control_key = None  # Variable to control the light switching
main_key = None # keeps function on traffic light

vehicle_count_cam1 = get_vehicle_count_cam1()
vehicle_count_cam2 = get_vehicle_count_cam2()

# Check the modes of the traffic lights
mode1, mode2 = check_mode()

# Display vehicle counts
print(f"Vehicle Count Camera 1: {vehicle_count_cam1}")
print(f"Vehicle Count Camera 2: {vehicle_count_cam2}")

# Sets which light goes green first after start up
if vehicle_count_cam1 > vehicle_count_cam2:
    main_key = 1
else:
    main_key = 2

try:
    while True:
        while mode1 == "Manual":  
            change_light(2, RED)
            time.sleep(DELAY_AFTER_RED)
            change_light(1, GREEN)
            while mode1 == "Manual":
                print("Traffic Light 1 in Manual Mode")
                time.sleep(DELAY_BETWEEN_CYCLES)
                mode1, mode2 = check_mode()
            
        while mode2 == "Manual":
            change_light(1, RED)
            time.sleep(DELAY_AFTER_RED)
            change_light(2, GREEN)
            while mode2 == "Manual":
                print("Traffic Light 2 remains green (Manual mode).")
                time.sleep(DELAY_BETWEEN_CYCLES)
                mode1, mode2 = check_mode()
            
        while main_key == 1 and mode1 == "Automatic" and mode2 == "Automatic":
            change_light(1, GREEN)
            change_light(2, RED)
            print("Traffic Light 1 is green.")
            time.sleep(DELAY_GREEN_MIN)  # Keep Traffic Light 1 green for the minimum time
            control_key = 1  # Set control_key for Traffic Light 1
            # Check the modes of the traffic lights
            mode1, mode2 = check_mode()
            while control_key == 1 and mode1 == "Automatic" and mode2 == "Automatic":
                # Fetch and print vehicle counts
                vehicle_count_cam2 = get_vehicle_count_cam2()  # Re-fetch vehicle count
                mode1, mode2 = check_mode()
                print(f"Vehicle Count Camera 2: {vehicle_count_cam2}")
                
                if vehicle_count_cam2 > 0:
                    # Transition to orange then red
                    change_light(1, ORANGE)
                    time.sleep(DELAY_ORANGE)
                    change_light(1, RED)
                    print("Traffic Light 1 is now red.")

                    # Delay before changing the other light
                    time.sleep(DELAY_AFTER_RED)
                    change_light(2, GREEN)
                    print("Traffic Light 2 is green.")
                    main_key = 2  # Switch main_key to Traffic Light 2
                    control_key = 2  # Update control_key for Traffic Light 2
                else:
                    print("Traffic Light 1 remains green.")
                    time.sleep(DELAY_BETWEEN_CYCLES)

        while main_key == 2 and mode1 == "Automatic" and mode2 == "Automatic":
            change_light(2, GREEN)
            change_light(1, RED)
            print("Traffic Light 2 is green.")
            time.sleep(DELAY_GREEN_MIN)
            control_key = 2  # Set control_key for Traffic Light 2
            # Check the modes of the traffic lights
            mode1, mode2 = check_mode()
            while control_key == 2 and mode1 == "Automatic" and mode2 == "Automatic":
                vehicle_count_cam1 = get_vehicle_count_cam1()
                mode1, mode2 = check_mode()
                print(f"Vehicle Count Camera 1: {vehicle_count_cam1}")
                
                if vehicle_count_cam1 > 0:
                    change_light(2, ORANGE)
                    time.sleep(DELAY_ORANGE)
                    change_light(2, RED)
                    print("Traffic Light 2 is now red.")

                    time.sleep(DELAY_AFTER_RED)
                    change_light(1, GREEN)
                    print("Traffic Light 1 is green.")
                    main_key = 1  # Switch to Traffic Light 1
                    control_key = 1  # Update control_key for Traffic Light 1
                else:
                    print("Traffic Light 2 remains green.")
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
