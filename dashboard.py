import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn
import rust_server  # our PyO3 module

app = FastAPI()

# Keep track of connected WebSocket clients.
connected_websockets = set()


@app.on_event("startup")
async def startup_event():
    # Start the Rust TCP server that receives frames.
    rust_server.start_tcp_server()
    # Start the background task to broadcast frames.
    asyncio.create_task(broadcast_frames())


async def broadcast_frames():
    while True:
        # Get the latest frame from the Rust module.
        frame = rust_server.get_latest_frame()
        if frame is not None:
            # Broadcast the frame to all connected WebSocket clients.
            to_remove = set()
            for ws in connected_websockets:
                try:
                    await ws.send_bytes(frame)
                except Exception:
                    to_remove.add(ws)
            for ws in to_remove:
                connected_websockets.discard(ws)
        await asyncio.sleep(0.03)  # ~30 FPS


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        while True:
            # Keep the connection alive.
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        connected_websockets.discard(websocket)


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Video Dashboard</title>
    </head>
    <body>
        <h1>Live Video Dashboard</h1>
        <img id="video" width="640" height="480" />
        <script>
            var ws = new WebSocket("ws://" + location.host + "/ws");
            ws.binaryType = "arraybuffer";
            ws.onmessage = function(event) {
                var blob = new Blob([event.data], {type: "image/jpeg"});
                document.getElementById("video").src = URL.createObjectURL(blob);
            };
        </script>
        <!-- You can extend the dashboard with additional HTML/JS here -->
    </body>
    </html>
    """
    return html_content


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
