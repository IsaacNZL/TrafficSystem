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
                mode1 = cursor.fetchone()[0] if cursor.fetchone() else None

                cursor.execute("SELECT Mode FROM TrafficCam2Mode")
                mode2 = cursor.fetchone()[0] if cursor.fetchone() else None

                return mode1, mode2
        finally:
            connection.close()

    def update_light_state(self, light_number, state):
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                query = f"INSERT INTO TrafficLight{light_number} (Colour) VALUES (%s)"
                cursor.execute(query, (state,))
            connection.commit()
        finally:
            connection.close()

    def delete_light_state(self, light_number):
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                query = f"DELETE FROM TrafficLight{light_number}"
                cursor.execute(query)
            connection.commit()
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

    def handle_automatic_mode(self, main_light):
        other_light = 1 if main_light == 2 else 2
        self.traffic_lights[main_light].change_light(TrafficLight.GREEN)
        self.traffic_lights[other_light].change_light(TrafficLight.RED)
        time.sleep(self.DELAY_GREEN_MIN)

        while self.db.fetch_modes() == ("Automatic", "Automatic"):
            vehicle_count = self.db.fetch_vehicle_count(other_light)
            print(f"Vehicle Count Camera {other_light}: {vehicle_count}")

            if vehicle_count > 0:
                self.traffic_lights[main_light].change_light(TrafficLight.ORANGE)
                time.sleep(self.DELAY_ORANGE)
                self.traffic_lights[main_light].change_light(TrafficLight.RED)
                time.sleep(self.DELAY_AFTER_RED)
                self.traffic_lights[other_light].change_light(TrafficLight.GREEN)
                break
            else:
                print(f"Traffic Light {main_light} remains green.")
                time.sleep(self.DELAY_BETWEEN_CYCLES)

    def run(self):
        self.traffic_lights[1].change_light(TrafficLight.RED)
        self.traffic_lights[2].change_light(TrafficLight.RED)

        try:
            while True:
                mode1, mode2 = self.db.fetch_modes()

                if mode1 == "Manual":
                    self.handle_manual_mode(1)
                elif mode2 == "Manual":
                    self.handle_manual_mode(2)
                elif mode1 == "Automatic" and mode2 == "Automatic":
                    self.handle_automatic_mode(1)
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
