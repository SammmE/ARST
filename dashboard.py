import asyncio
import datetime
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn
import rust_server  # our PyO3 module

from arst_brain import ARST

app = FastAPI()

# Keep track of connected WebSocket clients.
connected_websockets = set()

# Create a global instance of the ARST brain.
robot_brain = ARST()

CAM_FPS = 30  # Frames per second

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
            # Update the ARST brain with the latest frame.
            robot_brain.update_video_feed(frame)
            # Broadcast the frame to all connected WebSocket clients.
            to_remove = set()
            for ws in connected_websockets:
                try:
                    await ws.send_bytes(frame)
                except Exception:
                    to_remove.add(ws)
            for ws in to_remove:
                connected_websockets.discard(ws)
        # Use a dynamic sleep interval for desired FPS.
        await asyncio.sleep(1 / CAM_FPS)

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
        <title>TARS Live Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <!-- Optional: Bootstrap CSS for better styling -->
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css">
        <style>
            body { margin: 20px; }
            #video {
                width: 100%;
                max-width: 640px;
                height: auto;
                border: 2px solid #333;
            }
            #meta-panel {
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="mb-4">TARS Live Dashboard</h1>
            <div class="row">
                <div class="col-md-8">
                    <img id="video" src="" alt="Live video feed" />
                </div>
                <div class="col-md-4">
                    <div id="meta-panel" class="card">
                        <div class="card-header">
                            Robot Status &amp; Instructions
                        </div>
                        <div class="card-body">
                            <p id="meta-data">Loading...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    
        <script>
            // Establish WebSocket connection for the video stream.
            var ws = new WebSocket("ws://" + location.host + "/ws");
            ws.binaryType = "arraybuffer";
            ws.onmessage = function(event) {
                var blob = new Blob([event.data], {type: "image/jpeg"});
                document.getElementById("video").src = URL.createObjectURL(blob);
            };
    
            // Function to fetch meta data and update the meta panel.
            async function updateMeta() {
                try {
                    // Define a payload for /meta.
                    const payload = {
                        is_active: false,
                        active_prompt: ""
                    };
                    const response = await fetch("/meta", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });
                    const data = await response.json();
                    const metaText = "<strong>Timestamp:</strong> " + data.timestamp + "<br>" +
                                     "<strong>Instructions:</strong><br>" + data.instructions.join("<br>");
                    document.getElementById("meta-data").innerHTML = metaText;
                } catch (err) {
                    console.error("Error fetching meta data:", err);
                    document.getElementById("meta-data").innerHTML = "Error loading meta data.";
                }
            }
    
            // Poll the /meta endpoint every 2 seconds.
            setInterval(updateMeta, 2000);
            // Initial meta update.
            updateMeta();
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/meta")
async def get_meta(payload: dict):
    """
    Processes the meta payload using the ARST brain.

    Expected payload JSON:
    {
        "is_active": bool,
        "active_prompt": str
    }

    Returns a JSON response with:
        - instructions: list of instructions for the robot.
        - timestamp: when the response was generated.
    """
    instructions = robot_brain.process_meta(payload)
    return {
        "instructions": instructions,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
