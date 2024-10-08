import sys
import time
import pymysql  # Import the pymysql library for MariaDB
from time import sleep

# Connect to the MariaDB database
conn = pymysql.connect(
    host='localhost',
    user='write_user',
    password='write_password',
    database='practicedb'
)
c = conn.cursor()

# Delete previous data in the TrafficCam1 table
c.execute("DELETE FROM TrafficCam1")
conn.commit()

# Reset auto-increment ID back to 1
c.execute("ALTER TABLE TrafficCam1 AUTO_INCREMENT = 1")
conn.commit()

# Initialize vehicle counters
data = 0
car = 0
bus = 0
motorbike = 0

while True:
    print("starting next upload")
    data += 2
    car += 1
    bus += 3
    motorbike += 1
    date = time.strftime("%Y-%m-%d")  # current date, formatted as YYYY-MM-DD
    t = time.strftime("%H:%M:%S")  # current time
    # Insert data into the MariaDB table
    c.execute("INSERT INTO TrafficCam1 (VehicleCount, Date, Time, Car, Bus, Motorbike) VALUES (%s, %s, %s, %s, %s, %s)", (data, date, t, car, bus, motorbike))
    conn.commit()  # commit all changes to the database
    sleep(2)  # Sleep for 2 seconds before next insertion
