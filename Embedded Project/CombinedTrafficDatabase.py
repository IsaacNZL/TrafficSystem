import sys
import time
import pymysql  # Import the pymysql library for MariaDB
import cv2
import os
from time import sleep

# Connect to the MariaDB database
conn = pymysql.connect(
    host='localhost',
    user='write_user',
    password='write_password',
    database='practicedb'
)
c = conn.cursor()

# This is to pull the information about what each object is called
classNames = []
classFile = r'/home/pi64/Desktop/Object_Detection_Files/coco.names'
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

# This is to pull the information about what each object should look like
configPath = r'/home/pi64/Desktop/Object_Detection_Files/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'
weightsPath = r'/home/pi64/Desktop/Object_Detection_Files/frozen_inference_graph.pb'

# This is some setup values to get good results
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# This is to set up what the drawn box size/colour is and the font/size/colour of the name tag and confidence label
def getObjects(img, thres, nms, draw=True, objects=[]):
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    if len(objects) == 0: objects = classNames
    objectInfo = []
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            if className in objects:
                objectInfo.append([box, className])
                if draw:
                    cv2.rectangle(img, box, color=(0, 255, 0), thickness=2)
                    cv2.putText(img, classNames[classId - 1].upper(), (box[0] + 10, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(img, str(round(confidence * 100, 2)), (box[0] + 200, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

    return img, objectInfo

# Load the video file
video_path = r'/home/pi64/Documents/TrafficDataBase/CarVideos.mp4'  # path to video
cap = cv2.VideoCapture(video_path)

# Check if the video opened successfully
if not cap.isOpened():
    print("Error: Could not open video file.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("End of video file or error reading frame.")
        break

    # Reset the counters for vehicles for each frame
    car_count = 0
    bus_count = 0
    motorcycle_count = 0
    total_vehicles = 0

    # Run object detection on the current frame
    result, objectInfo = getObjects(frame, 0.6, 0.2, objects=['car', 'motorcycle', 'bus'])

    # Count the number of detected vehicles in the current frame
    for obj in objectInfo:
        if obj[1] == 'car':
            car_count += 1
        elif obj[1] == 'bus':
            bus_count += 1
        elif obj[1] == 'motorcycle':
            motorcycle_count += 1

    total_vehicles = car_count + bus_count + motorcycle_count

    # Print the counts for each vehicle type for the current frame
    print(f"VehicleCount: {total_vehicles} | Cars: {car_count} | Buses: {bus_count} | Motorcycles: {motorcycle_count}")

    # Get current date and time
    date = time.strftime("%Y-%m-%d")  # current date, formatted as YYYY-MM-DD
    t = time.strftime("%H:%M:%S")  # current time

    # Insert data into the MariaDB table
    c.execute("INSERT INTO TrafficCam1 (VehicleCount, Date, Time, Car, Bus, Motorbike) VALUES (%s, %s, %s, %s, %s, %s)",
              (total_vehicles, date, t, car_count, bus_count, motorcycle_count))
    conn.commit()  # commit all changes to the database

    # Resize the frame to make it smaller (e.g., 50% of the original size)
    frame_resized = cv2.resize(result, (int(result.shape[1] * 0.45), int(result.shape[0] * 0.45)))

    # Show the resized results
    cv2.imshow("Output", frame_resized)

    # Press 'q' to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and close all windows
cap.release()
conn.close()  # Close the database connection
cv2.destroyAllWindows()
