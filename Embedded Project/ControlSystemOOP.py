import time
import RPi.GPIO as GPIO
import pymysql


# Class to handle database connections and queries
class DatabaseConnection:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def get_connection(self):
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )

    def fetch_vehicle_count(self, camera_num):
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                table = f"TrafficCam{camera_num}"
                query = f"SELECT VehicleCount FROM {table} ORDER BY Date DESC, Time DESC LIMIT 1"
                cursor.execute(query)
                result = cursor.fetchone()
                return result[0] if result else 0
        finally:
            connection.close()

    def fetch_modes(self):
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT Mode FROM TrafficCam1Mode")
                mode1_result = cursor.fetchone()
                mode1 = mode1_result[0] if mode1_result else None

                cursor.execute("SELECT Mode FROM TrafficCam2Mode")
                mode2_result = cursor.fetchone()
                mode2 = mode2_result[0] if mode2_result else None

                return mode1, mode2
        finally:
            connection.close()

    def update_light_state(self, light_number, state):
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                # Delete current light state before updating
                delete_query = f"DELETE FROM TrafficLight{light_number}"
                cursor.execute(delete_query)
                connection.commit()
                
                # Insert new light state
                insert_query = f"INSERT INTO TrafficLight{light_number} (Colour) VALUES (%s)"
                cursor.execute(insert_query, (state,))
                connection.commit()
                print(f"Updated TrafficLight{light_number} state to {state}")  # Debug statement
        finally:
            connection.close()


# Class to handle the operations of a single traffic light
class TrafficLight:
    RED = "RED"
    GREEN = "GREEN"
    ORANGE = "ORANGE"

    def __init__(self, light_number, pins, db):
        self.light_number = light_number
        self.pins = pins
        self.db = db
        GPIO.setmode(GPIO.BCM)
        for pin in pins.values():
            GPIO.setup(pin, GPIO.OUT)

    def change_light(self, state):
        print(f"Traffic Light {self.light_number} is now {state}")
        for color, pin in self.pins.items():
            GPIO.output(pin, color == state)
        self.db.update_light_state(self.light_number, state)

    def clear_light(self):
        for pin in self.pins.values():
            GPIO.output(pin, GPIO.LOW)


# Class to manage the entire traffic light system
class TrafficLightSystem:
    DELAY_GREEN_MIN = 6
    DELAY_ORANGE = 3
    DELAY_RED = 2
    DELAY_BETWEEN_CYCLES = 2
    DELAY_AFTER_RED = 2

    def __init__(self, db):
        self.db = db
        self.traffic_lights = {
            1: TrafficLight(1, {"RED": 17, "ORANGE": 27, "GREEN": 22}, db),
            2: TrafficLight(2, {"RED": 18, "ORANGE": 23, "GREEN": 25}, db),
        }

    def handle_manual_mode(self, light_number):
        other_light = 2 if light_number == 1 else 1
        self.traffic_lights[other_light].change_light(TrafficLight.RED)
        time.sleep(self.DELAY_AFTER_RED)
        self.traffic_lights[light_number].change_light(TrafficLight.GREEN)

        while self.db.fetch_modes()[light_number - 1] == "Manual":
            print(f"Traffic Light {light_number} in Manual Mode")
            time.sleep(self.DELAY_BETWEEN_CYCLES)

    def handle_automatic_mode(self):
        """ Alternate between the two traffic lights in automatic mode. """
        current_light = 1  # Start with Traffic Light 1
        other_light = 2

        while self.db.fetch_modes() == ("Automatic", "Automatic"):
            print(f"Switching Traffic Light {current_light} to GREEN")
            # Green for current_light, Red for other_light
            self.traffic_lights[current_light].change_light(TrafficLight.GREEN)
            self.traffic_lights[other_light].change_light(TrafficLight.RED)
            time.sleep(self.DELAY_GREEN_MIN)

            vehicle_count_other = self.db.fetch_vehicle_count(other_light)
            print(f"Vehicle Count Camera {other_light}: {vehicle_count_other}")

            if vehicle_count_other > 0:
                # Transition current_light from green to orange to red
                self.traffic_lights[current_light].change_light(TrafficLight.ORANGE)
                time.sleep(self.DELAY_ORANGE)
                self.traffic_lights[current_light].change_light(TrafficLight.RED)
                time.sleep(self.DELAY_AFTER_RED)

                # Swap the lights for the next cycle
                current_light, other_light = other_light, current_light  # Swap roles
                time.sleep(self.DELAY_BETWEEN_CYCLES)
            else:
                print(f"Traffic Light {current_light} remains green.")
                time.sleep(self.DELAY_BETWEEN_CYCLES)

    def run(self):
        # Initial state: both traffic lights start red
        self.traffic_lights[1].change_light(TrafficLight.RED)
        self.traffic_lights[2].change_light(TrafficLight.RED)

        try:
            while True:
                # Fetch the modes for both lights (Manual or Automatic)
                mode1, mode2 = self.db.fetch_modes()

                # If Traffic Light 1 is in manual mode
                if mode1 == "Manual":
                    self.handle_manual_mode(1)
                # If Traffic Light 2 is in manual mode
                elif mode2 == "Manual":
                    self.handle_manual_mode(2)
                # If both Traffic Lights are in automatic mode
                elif mode1 == "Automatic" and mode2 == "Automatic":
                    self.handle_automatic_mode()  # Alternate between the lights
                time.sleep(self.DELAY_BETWEEN_CYCLES)

        except KeyboardInterrupt:
            print("Traffic control program interrupted.")
        finally:
            GPIO.cleanup()


# Main Program Execution
if __name__ == "__main__":
    db = DatabaseConnection(host='localhost', user='username', password='password', database='practicedb')
    system = TrafficLightSystem(db)
    system.run()
