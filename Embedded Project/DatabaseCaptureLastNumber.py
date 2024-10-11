import pymysql
import time

# Database connection details
db_host = '172.29.2.64'  # Replace with your Raspberry Pi's IP address
db_user = 'read_user'       # Replace with your MariaDB username
db_password = 'read_password'   # Replace with your MariaDB password
db_name = 'practicedb'     # Replace with your database name

# Connect to the MariaDB database
conn = pymysql.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name
)

# Create a cursor object
c = conn.cursor()

# Set the transaction isolation level to READ COMMITTED
c.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")

# Start an infinite loop that checks the data every 5 seconds
while True:
    # Fetch the most recent VehicleCount value based on Date and Time
    c.execute("SELECT VehicleCount FROM TrafficCam1 ORDER BY Date DESC, Time DESC LIMIT 1")

    # Fetch the single row
    row = c.fetchone()

    if row:  # Ensure there is a result
        data_capture = row[0]  # The most recent VehicleCount value
        print("Latest VehicleCount data:", data_capture)
    else:
        print("No data available in the table.")

    # Wait for 5 seconds before checking again
    time.sleep(2)

# Close the database connection when the loop is interrupted
conn.close()
