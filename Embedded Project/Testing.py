import sys
import time
import pymysql  # Import the pymysql library for MariaDB
import cv2
import threading
from queue import Queue
from picamera2 import Picamera2  # Import the Picamera2 library

# Database connection details
db_conn = pymysql.connect(
    host='localhost',
    user='write_user',
    password='write_password',
    database='practicedb'
)
c = db_conn.cursor()

# Delete previous data in the TrafficCam1 table
c.execute("DELETE FROM TrafficCam1")
db_conn.commit()

# Reset auto-increment ID back to 1
c.execute("ALTER TABLE TrafficCam1 AUTO_INCREMENT = 1")
db_conn.commit()

# Queues for frame communication between threads
frame_queue = Queue()
processed_frame_queue = Queue()

# Stop flag for signaling both threads to stop
stop_flag = False

# This is to pull the information about what each object is called
classNames = []
classFile = r'/home/pi64/Desktop/Object_Detection_Files/coco.names'
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

# This is to pull the information about what each object should look like
configPath = r'/home/pi64/Desktop/Object_Detection_Files/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'
weightsPath = r'/home/pi64/Desktop/Object_Detection_Files/frozen_inference_graph.pb'

# Setup the detection model
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Function to set up object detection drawing on the frame
def getObjects(img, thres, nms, draw=True, objects=[]):
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    if len(objects) == 0:
        objects = classNames
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

# Function for the object detection thread
def process_frames():
    global stop_flag
    while not stop_flag:
        try:
            frame = frame_queue.get(timeout=1)  # Allow it to break if queue is empty for a while
        except:
            continue
        if frame is None:
            break  # Stop if None is received

        # Perform object detection and draw bounding boxes
        frame_with_boxes, objectInfo = getObjects(frame, 0.6, 0.2, objects=['car', 'motorcycle', 'bus'])

        # Count the vehicles for the frame
        car_count = sum(1 for obj in objectInfo if obj[1] == 'car')
        bus_count = sum(1 for obj in objectInfo if obj[1] == 'bus')
        motorcycle_count = sum(1 for obj in objectInfo if obj[1] == 'motorcycle')

        total_vehicles = car_count + bus_count + motorcycle_count

        # Get the current time
        date = time.strftime("%Y-%m-%d")
        current_time = time.strftime("%H:%M:%S")

        # Add the processed frame to the processed_frame_queue for display
        processed_frame_queue.put((frame_with_boxes, total_vehicles, car_count, bus_count, motorcycle_count, date, current_time))
        
        frame_queue.task_done()

# Initialize the PiCamera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

# Start the object detection thread
process_thread = threading.Thread(target=process_frames)
process_thread.start()

# Main loop for capturing frames every 3 seconds and displaying processed frames
try:
    while True:
        # Capture a frame from the Pi camera every 3 seconds
        img = picam2.capture_array("main")
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # Convert from BGRA to BGR

        frame_queue.put(img)  # Put the captured frame into the queue

        # Display the processed frame (with bounding boxes) once available
        if not processed_frame_queue.empty():
            processed_frame, total_vehicles, car_count, bus_count, motorcycle_count, date, current_time = processed_frame_queue.get()

            # Print vehicle counts for the current frame
            print(f"VehicleCount: {total_vehicles} | Cars: {car_count} | Buses: {bus_count} | Motorcycles: {motorcycle_count}")

            # Upload vehicle counts to the database
            c.execute(
                "INSERT INTO TrafficCam1 (VehicleCount, Date, Time, Car, Bus, Motorbike) VALUES (%s, %s, %s, %s, %s, %s)",
                (total_vehicles, date, current_time, car_count, bus_count, motorcycle_count))
            db_conn.commit()  # Commit all changes to the database

            # Resize frame for display
            frame_resized = cv2.resize(processed_frame, (int(processed_frame.shape[1] * 0.45), int(processed_frame.shape[0] * 0.45)))
            cv2.imshow("Output", frame_resized)

        # Wait for 3 seconds
        time.sleep(3)

        # Exit when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_flag = True
            break
finally:
    # Stop the object detection thread
    frame_queue.put(None)
    process_thread.join()

    # Cleanup
    picam2.stop()  # Stop the camera
    db_conn.close()
    cv2.destroyAllWindows()
