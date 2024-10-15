import sys
import time
import pymysql  # Import the pymysql library for MariaDB
import cv2
import threading
from queue import Queue
from picamera2 import Picamera2  # Import the Picamera2 library


# Database handler class for managing database operations
class DatabaseHandler:
    def __init__(self, host, user, password, database):
        self.connection = pymysql.connect(host=host, user=user, password=password, database=database)
        self.cursor = self.connection.cursor()

    def initialize_table(self, table_name):
        # Delete previous data and reset auto-increment ID
        self.cursor.execute(f"DELETE FROM {table_name}")
        self.connection.commit()
        self.cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1")
        self.connection.commit()

    def insert_vehicle_data(self, table_name, total_vehicles, car_count, bus_count, motorcycle_count, date, time):
        query = f"INSERT INTO {table_name} (VehicleCount, Date, Time, Car, Bus, Motorbike) VALUES (%s, %s, %s, %s, %s, %s)"
        self.cursor.execute(query, (total_vehicles, date, time, car_count, bus_count, motorcycle_count))
        self.connection.commit()

    def close(self):
        self.connection.close()


# Class for setting up the object detection model
class ObjectDetectionModel:
    def __init__(self, class_file, config_path, weights_path):
        self.class_names = self.load_class_names(class_file)
        self.net = self.setup_model(config_path, weights_path)

    def load_class_names(self, class_file):
        with open(class_file, "rt") as f:
            return f.read().rstrip("\n").split("\n")

    def setup_model(self, config_path, weights_path):
        net = cv2.dnn_DetectionModel(weights_path, config_path)
        net.setInputSize(320, 320)
        net.setInputScale(1.0 / 127.5)
        net.setInputMean((127.5, 127.5, 127.5))
        net.setInputSwapRB(True)
        return net

    def detect_objects(self, img, thres, nms, objects=['car', 'motorcycle', 'bus'], draw=True):
        class_ids, confs, bbox = self.net.detect(img, confThreshold=thres, nmsThreshold=nms)
        object_info = []

        if len(class_ids) != 0:
            for class_id, confidence, box in zip(class_ids.flatten(), confs.flatten(), bbox):
                class_name = self.class_names[class_id - 1]
                if class_name in objects:
                    object_info.append([box, class_name])
                    if draw:
                        cv2.rectangle(img, box, color=(0, 255, 0), thickness=2)
                        cv2.putText(img, class_name.upper(), (box[0] + 10, box[1] + 30), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(img, str(round(confidence * 100, 2)), (box[0] + 200, box[1] + 30), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
        return img, object_info


# Thread handler for processing frames
class FrameProcessor(threading.Thread):
    def __init__(self, frame_queue, processed_frame_queue, model):
        threading.Thread.__init__(self)
        self.frame_queue = frame_queue
        self.processed_frame_queue = processed_frame_queue
        self.model = model
        self.stop_flag = False

    def run(self):
        while not self.stop_flag:
            try:
                frame = self.frame_queue.get(timeout=1)
            except:
                continue
            if frame is None:
                break

            # Perform object detection and draw bounding boxes
            frame_with_boxes, object_info = self.model.detect_objects(frame, 0.6, 0.2)

            # Count the vehicles for the frame
            car_count = sum(1 for obj in object_info if obj[1] == 'car')
            bus_count = sum(1 for obj in object_info if obj[1] == 'bus')
            motorcycle_count = sum(1 for obj in object_info if obj[1] == 'motorcycle')
            total_vehicles = car_count + bus_count + motorcycle_count

            # Get the current time
            date = time.strftime("%Y-%m-%d")
            current_time = time.strftime("%H:%M:%S")

            # Put the processed frame in the processed_frame_queue
            self.processed_frame_queue.put((frame_with_boxes, total_vehicles, car_count, bus_count, motorcycle_count, date, current_time))

            self.frame_queue.task_done()


# Pi Camera handler class
class PiCameraHandler:
    def __init__(self):
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
        self.picam2.start()

    def capture_frame(self):
        img = self.picam2.capture_array("main")
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def stop(self):
        self.picam2.stop()


# Main traffic monitoring system class
class TrafficMonitoringSystem:
    def __init__(self, db_handler, model, camera_handler):
        self.db_handler = db_handler
        self.model = model
        self.camera_handler = camera_handler
        self.frame_queue = Queue()
        self.processed_frame_queue = Queue()
        self.processor_thread = FrameProcessor(self.frame_queue, self.processed_frame_queue, model)
        self.processor_thread.start()

    def run(self):
        try:
            while True:
                # Capture a frame every 3 seconds
                img = self.camera_handler.capture_frame()
                self.frame_queue.put(img)

                # Display the processed frame once available
                if not self.processed_frame_queue.empty():
                    processed_frame, total_vehicles, car_count, bus_count, motorcycle_count, date, current_time = self.processed_frame_queue.get()

                    # Print vehicle counts
                    print(f"VehicleCount: {total_vehicles} | Cars: {car_count} | Buses: {bus_count} | Motorcycles: {motorcycle_count}")

                    # Upload vehicle counts to the database
                    self.db_handler.insert_vehicle_data("TrafficCam1", total_vehicles, car_count, bus_count, motorcycle_count, date, current_time)

                    # Display the frame
                    frame_resized = cv2.resize(processed_frame, (int(processed_frame.shape[1] * 0.45), int(processed_frame.shape[0] * 0.45)))
                    cv2.imshow("Output", frame_resized)

                # Wait for 3 seconds
                time.sleep(3)

                # Exit when 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.processor_thread.stop_flag = True
                    break
        finally:
            # Stop the processor thread and clean up
            self.frame_queue.put(None)
            self.processor_thread.join()
            self.camera_handler.stop()
            self.db_handler.close()
            cv2.destroyAllWindows()


# Main program entry point
if __name__ == "__main__":
    db_handler = DatabaseHandler(host='10.62.135.185', user='trafficcamera1', password='1234', database='practicedb')
    db_handler.initialize_table("TrafficCam1")

    model = ObjectDetectionModel(
        class_file=r'/home/pi64/Desktop/Object_Detection_Files/coco.names',
        config_path=r'/home/pi64/Desktop/Object_Detection_Files/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt',
        weights_path=r'/home/pi64/Desktop/Object_Detection_Files/frozen_inference_graph.pb'
    )

    camera_handler = PiCameraHandler()
    system = TrafficMonitoringSystem(db_handler, model, camera_handler)
    system.run()
