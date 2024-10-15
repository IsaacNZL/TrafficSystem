import time
import RPi.GPIO as GPIO
import pymysql

# GPIO pin setup for Traffic Light 1
RED_LED_PIN_1 = 17
ORANGE_LED_PIN_1 = 27
GREEN_LED_PIN_1 = 22

# GPIO pin setup for Traffic Light 2
RED_LED_PIN_2 = 18
ORANGE_LED_PIN_2 = 23
GREEN_LED_PIN_2 = 25

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([RED_LED_PIN_1, ORANGE_LED_PIN_1, GREEN_LED_PIN_1,
             RED_LED_PIN_2, ORANGE_LED_PIN_2, GREEN_LED_PIN_2], GPIO.OUT)

# Traffic light state constants
RED = "RED"
GREEN = "GREEN"
ORANGE = "ORANGE"

# Time delays in seconds for the light states
DELAY_GREEN_MIN = 6
DELAY_ORANGE = 3
DELAY_RED = 2
DELAY_BETWEEN_CYCLES = 2
DELAY_AFTER_RED = 2

# Database connection
def get_db_connection():
    return pymysql.connect(host='localhost', user='username', password='password', database='practicedb')

# Fetch vehicle count from the database for specified camera
def get_vehicle_count(camera_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = f"SELECT VehicleCount FROM TrafficCam{camera_id} ORDER BY Date DESC, Time DESC LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else 0
    finally:
        connection.close()

# Check the mode of each traffic camera
def check_modes():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            mode1 = cursor.execute("SELECT Mode FROM TrafficCam1Mode").fetchone()
            mode2 = cursor.execute("SELECT Mode FROM TrafficCam2Mode").fetchone()
            return (mode1[0] if mode1 else None, mode2[0] if mode2 else None)
    finally:
        connection.close()

# Change traffic light states and update GPIO
def change_light(light_number, state):
    print(f"Traffic Light {light_number} is now {state}")
    if light_number == 1:
        GPIO.output(RED_LED_PIN_1, state == RED)
        GPIO.output(ORANGE_LED_PIN_1, state == ORANGE)
        GPIO.output(GREEN_LED_PIN_1, state == GREEN)
    elif light_number == 2:
        GPIO.output(RED_LED_PIN_2, state == RED)
        GPIO.output(ORANGE_LED_PIN_2, state == ORANGE)
        GPIO.output(GREEN_LED_PIN_2, state == GREEN)

    delete_light_mode(light_number)
    send_light_state_to_db(light_number, state)

def delete_light_mode(light_number):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM TrafficLight{light_number}")
        connection.commit()
    finally:
        connection.close()

def send_light_state_to_db(light_number, state):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"INSERT INTO TrafficLight{light_number} (Colour) VALUES (%s)", (state,))
        connection.commit()
    finally:
        connection.close()

# Set both traffic lights to RED initially
change_light(1, RED)
change_light(2, RED)

# Main loop
try:
    while True:
        mode1, mode2 = check_modes()
        vehicle_count_cam1 = get_vehicle_count(1)
        vehicle_count_cam2 = get_vehicle_count(2)

        print(f"Vehicle Count Camera 1: {vehicle_count_cam1}, Camera 2: {vehicle_count_cam2}")

        if mode1 == "Manual":
            change_light(2, RED)
            time.sleep(DELAY_AFTER_RED)
            change_light(1, GREEN)
            while mode1 == "Manual":
                print("Traffic Light 1 in Manual Mode")
                time.sleep(DELAY_BETWEEN_CYCLES)

        elif mode2 == "Manual":
            change_light(1, RED)
            time.sleep(DELAY_AFTER_RED)
            change_light(2, GREEN)
            while mode2 == "Manual":
                print("Traffic Light 2 in Manual Mode")
                time.sleep(DELAY_BETWEEN_CYCLES)

        else:  # Automatic mode
            if vehicle_count_cam1 > vehicle_count_cam2:
                current_light = 1
            else:
                current_light = 2

            while True:
                change_light(current_light, GREEN)
                time.sleep(DELAY_GREEN_MIN)

                if current_light == 1:
                    change_light(current_light, ORANGE)
                    time.sleep(DELAY_ORANGE)
                    change_light(current_light, RED)
                    time.sleep(DELAY_AFTER_RED)
                    current_light = 2
                else:
                    change_light(current_light, ORANGE)
                    time.sleep(DELAY_ORANGE)
                    change_light(current_light, RED)
                    time.sleep(DELAY_AFTER_RED)
                    current_light = 1

except KeyboardInterrupt:
    print("Traffic control program interrupted.")

finally:
    # Turn off all LEDs when the program ends
    GPIO.output([RED_LED_PIN_1, ORANGE_LED_PIN_1, GREEN_LED_PIN_1,
                  RED_LED_PIN_2, ORANGE_LED_PIN_2, GREEN_LED_PIN_2], GPIO.LOW)
    GPIO.cleanup()
