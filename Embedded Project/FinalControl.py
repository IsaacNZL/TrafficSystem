import time
import RPi.GPIO as GPIO
import pymysql

# GPIO pin setup for traffic lights
TRAFFIC_LIGHTS = {
    1: {"RED": 17, "ORANGE": 27, "GREEN": 22},
    2: {"RED": 18, "ORANGE": 23, "GREEN": 25}
}

# setup GPIO - for the traffic light model that was built
GPIO.setmode(GPIO.BCM)
for pins in TRAFFIC_LIGHTS.values():
    for pin in pins.values():
        GPIO.setup(pin, GPIO.OUT)

# traffic light state constants
RED = "RED"
GREEN = "GREEN"
ORANGE = "ORANGE"

last_green_light = None 
control_key = None 
main_key = None 

DELAY_GREEN_MIN = 6  # minimum time the light stays green
DELAY_ORANGE = 3  # time the light stays orange before turning red
DELAY_RED = 2  # time the light stays red after turning from green
DELAY_BETWEEN_CYCLES = 2  # delay between each cycle of checking
DELAY_AFTER_RED = 2  # delay after turning red before changing the other light

# database connection function
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='username',
        password='password',
        database='practicedb'
    )

# fetch vehicle count from the database for a specified camera
def get_vehicle_count(camera_num):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            table = f"TrafficCam{camera_num}"  # set table that is required
            query = f"SELECT VehicleCount FROM {table} ORDER BY Date DESC, Time DESC LIMIT 1" # receives the latest data uploaded
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else 0
    finally:
        connection.close()

# check the mode of each traffic camera
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

# switching between light states for both traffic lights
def change_light(light_number, state):
    print(f"Traffic Light {light_number} is now {state}")
    for color, pin in TRAFFIC_LIGHTS[light_number].items():
        GPIO.output(pin, color == state)

    delete_light_mode(light_number)
    send_light_state_to_db(light_number, state)

# removing previously stored data from table
def delete_light_mode(light_number):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = f"DELETE FROM TrafficLight{light_number}"
            cursor.execute(query)
        connection.commit() 
    finally:
        connection.close()

# function to send the current light state to the database
def send_light_state_to_db(light_number, state):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = f"INSERT INTO TrafficLight{light_number} (Colour) VALUES (%s)"
            cursor.execute(query, (state,)) 
        connection.commit()
    finally:
        connection.close()
        
# function if either manual button is pressed
def handle_manual_mode(light_number):
    if light_number == 1:
        change_light(2, RED)
        time.sleep(DELAY_AFTER_RED)
        change_light(1, GREEN)
    else:
        change_light(1, RED)
        time.sleep(DELAY_AFTER_RED)
        change_light(2, GREEN)

    while check_mode()[light_number - 1] == "Manual":
        print(f"Traffic Light {light_number} in Manual Mode")
        time.sleep(DELAY_BETWEEN_CYCLES)

# function when auto mode is set 
def handle_automatic_mode(main_key, vehicle_count_getter, other_light):
    current_light = main_key
    other_light = 1 if current_light == 2 else 2
    
    # change lights based on main_key
    change_light(current_light, GREEN)
    change_light(other_light, RED)
    time.sleep(DELAY_GREEN_MIN)

    # loop while in automatic mode
    control_key = current_light
    while check_mode() == ("Automatic", "Automatic"):
        vehicle_count = vehicle_count_getter()  
        print(f"Vehicle Count Camera {other_light}: {vehicle_count}")
        
        #check if other traffic camera sees vehicles
        if vehicle_count > 0:
            # transition to orange then red
            change_light(current_light, ORANGE)
            time.sleep(DELAY_ORANGE)
            change_light(current_light, RED)
            time.sleep(DELAY_AFTER_RED)
            change_light(other_light, GREEN)
            main_key = other_light
            break  
        else:
            print(f"Traffic Light {current_light} remains green.")
            time.sleep(DELAY_BETWEEN_CYCLES)

    return main_key  # return updated main_key after switching lights

# for start up up both lights are red
change_light(1, RED)
change_light(2, RED)

# check vehicle count for start up
vehicle_count_cam1 = get_vehicle_count(1)
vehicle_count_cam2 = get_vehicle_count(2)

# check if set in manual or auto for start up
mode1, mode2 = check_mode()

# Display vehicle counts
print(f"Vehicle Count Camera 1: {vehicle_count_cam1}")
print(f"Vehicle Count Camera 2: {vehicle_count_cam2}")

# main while loop, constantly checking if the monitor page has activated manual mode or auto
try:
    while True:
        mode1, mode2 = check_mode()

        # traffic light 1 manual mode
        if mode1 == "Manual":
            handle_manual_mode(1)

        # traffic light 2 manual mode
        elif mode2 == "Manual":
            handle_manual_mode(2)

        # when set in auto mode, using lambda so we dont need a return
        elif mode1 == "Automatic" and mode2 == "Automatic":
            if main_key == 1:
                main_key = handle_automatic_mode(1, lambda: get_vehicle_count(2), 2)  
            else:
                main_key = handle_automatic_mode(2, lambda: get_vehicle_count(1), 1)  

except KeyboardInterrupt:
    print("Traffic control program interrupted.")

finally:
    # clear GPIO pins 
    for pins in TRAFFIC_LIGHTS.values():
        for pin in pins.values():
            GPIO.output(pin, GPIO.LOW)
    GPIO.cleanup()

