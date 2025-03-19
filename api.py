# dashboard_api.py
import threading
import socket
import pickle
import struct
import asyncio
import cv2

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# A set to hold active WebSocket connections
connected_websockets = set()

# This will be set to the FastAPI event loop on startup.
event_loop = None


@app.on_event("startup")
async def startup_event():
    global event_loop
    event_loop = asyncio.get_event_loop()
    # Start the low-latency TCP socket server in a background thread.
    threading.Thread(target=socket_server, daemon=True).start()


def socket_server():
    """A low‑latency TCP server that receives frames and broadcasts them to websockets."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 8888))
    server_socket.listen(5)
    print("TCP Socket Server listening on port 8888...")
    client_socket, client_address = server_socket.accept()
    print(f"TCP connection from {client_address} accepted")

    data = b""
    payload_size = struct.calcsize("Q")
    while True:
        # Receive the message size first.
        while len(data) < payload_size:
            packet = client_socket.recv(4 * 1024)  # 4K buffer
            if not packet:
                return
            data += packet
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        # Now retrieve the full frame data.
        while len(data) < msg_size:
            data += client_socket.recv(4 * 1024)
        frame_data = data[:msg_size]
        data = data[msg_size:]

        # Unpickle the frame (an OpenCV image)
        try:
            frame = pickle.loads(frame_data)
        except Exception as e:
            print("Error unpickling frame:", e)
            continue

        # Compress the frame as JPEG (for lower bandwidth over WebSocket)
        ret, jpeg = cv2.imencode(".jpg", frame)
        if not ret:
            continue
        jpeg_bytes = jpeg.tobytes()

        # Broadcast this JPEG frame to all connected websockets.
        if event_loop:
            asyncio.run_coroutine_threadsafe(broadcast_frame(jpeg_bytes), event_loop)


async def broadcast_frame(frame_bytes: bytes):
    """Send the frame bytes to every connected WebSocket client."""
    to_remove = set()
    for ws in connected_websockets:
        try:
            await ws.send_bytes(frame_bytes)
        except Exception as e:
            print("Error sending frame over WebSocket:", e)
            to_remove.add(ws)
    # Clean up any closed connections.
    for ws in to_remove:
        connected_websockets.discard(ws)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint that clients connect to for the live feed."""
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        # Keep the connection alive.
        while True:
            # Optionally, you can receive messages from the client if needed.
            await websocket.receive_text()
    except Exception as e:
        print("WebSocket disconnected:", e)
    finally:
        connected_websockets.discard(websocket)


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """A simple HTML dashboard with JavaScript to connect to the WebSocket."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Dashboard</title>
    </head>
    <body>
        <h1>Live Video Dashboard</h1>
        <img id="video" width="640" height="480" />
        <script>
            var ws = new WebSocket("ws://" + location.host + "/ws");
            ws.binaryType = "arraybuffer";
            ws.onmessage = function(event) {
                var bytes = new Uint8Array(event.data);
                var blob = new Blob([bytes], {type: "image/jpeg"});
                var url = URL.createObjectURL(blob);
                document.getElementById("video").src = url;
            };
        </script>
        <!-- Extend the dashboard here (add controls, analytics, etc.) -->
    </body>
    </html>
    """
    return html_content


if __name__ == "__main__":
    # Run the FastAPI server on port 8000.
    uvicorn.run(app, host="0.0.0.0", port=8000)
