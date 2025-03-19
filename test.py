# video_client.py
import cv2
import socket
import pickle
import struct

# Connect to the TCP server (dashboard_api.py)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 8888))  # Adjust the IP if needed

# Open the webcam (device 0).
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit(1)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    # Serialize the frame using pickle.
    frame_data = pickle.dumps(frame)
    # Pack the size of the frame.
    message_size = struct.pack("Q", len(frame_data))
    # Send size and data.
    client_socket.sendall(message_size)
    client_socket.sendall(frame_data)
    
    # (Optional) Also display locally.
    cv2.imshow('Local Webcam Feed', frame)
    if cv2.waitKey(1) == 13:  # Press Enter (key code 13) to quit.
        break

cap.release()
cv2.destroyAllWindows()
