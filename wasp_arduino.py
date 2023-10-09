import os
import cv2
from ultralytics import YOLO
import serial
import time

# Configurations
VIDEOS_DIR = os.path.join('.', 'videos')
video_path = os.path.join(VIDEOS_DIR, 'wasp_vid_001.mp4')
video_path_out = '{}_out.mp4'.format(video_path)
model_path = os.path.join('.', 'runs', 'detect', 'train', 'weights', 'last.pt')
threshold = 0.2

# Video Capture and Output
cap = cv2.VideoCapture(video_path)
ret, frame = cap.read()
H, W, _ = frame.shape
out = cv2.VideoWriter(video_path_out, cv2.VideoWriter_fourcc(*'MP4V'), int(cap.get(cv2.CAP_PROP_FPS)), (W, H))

# Load YOLO model
model = YOLO(model_path)

# Initialize the Serial Connection to Arduino
arduino = serial.Serial('COM3', 4800)

# Variable to track whether a wasp is detected
wasp_detected = False

# Process the video and label wasps
while ret:
    results = model(frame)[0]

    for result in results.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = result

        if score > threshold and results.names[int(class_id)] == 'wasp':
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
            cv2.putText(frame, results.names[int(class_id)].upper(), (int(x1), int(y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3, cv2.LINE_AA)
            
            # Set the wasp_detected flag to True
            wasp_detected = True

    out.write(frame)
    ret, frame = cap.read()

# Check if a wasp is detected
if wasp_detected:
    # Send a signal to Arduino
    arduino.write(b'1')  # You can use any suitable signal
    print('Sent signal to Arduino')

    # Wait for Arduino to signal completion
    response = arduino.readline().decode('utf-8').strip()
    if response == "Motor_started":
        print("Arduino has received the signal")

    # Continue to check for cycle completion
    while True:
        cresponse = arduino.readline().decode('utf-8').strip()
        if cresponse == "cycle_completed":
            print("Arduino has completed the cycle")
            break  # Exit the loop when the cycle is completed

    # Close the Serial Connection
    arduino.close()
else:
    print("No wasp detected in the video")

# Release video resources
cap.release()
out.release()
cv2.destroyAllWindows()