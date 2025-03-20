import cv2
import socket
import struct
import requests  # To send the dummy /meta call

# Connect to the TCP server (running in the Rust module on port 8888)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("localhost", 8888))  # Change as needed
META_PATH = "http://localhost:8000/meta"

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit(1)

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    # Encode the frame as JPEG.
    ret, jpeg = cv2.imencode(".jpg", frame)
    if not ret:
        continue
    data = jpeg.tobytes()
    # First send the size of the frame (8-byte little-endian)
    client_socket.sendall(struct.pack("Q", len(data)))
    # Then send the actual JPEG data.
    client_socket.sendall(data)

    frame_count += 1
    # Every 100 frames, send a dummy /meta call.
    if frame_count % 100 == 0:
        payload = {"is_active": False, "active_prompt": ""}
        try:
            response = requests.post(META_PATH, json=payload)
            print("Dummy /meta response:", response.json())
        except Exception as e:
            print("Error sending dummy /meta call:", e)

cap.release()
client_socket.close()
cv2.destroyAllWindows()
