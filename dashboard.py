import asyncio
import datetime
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn
import rust_server  # our PyO3 module

from arst_brain import ARST

app = FastAPI()

# Set of connected WebSocket clients for video streaming.
connected_websockets = set()

# Global instance of the ARST brain.
robot_brain = ARST()

CAM_FPS = 30  # Frames per second

with open("dashboard.html", "r") as f:
    DASHBOARD_HTML = f.read()


@app.on_event("startup")
async def startup_event():
    # Start the Rust TCP server that receives frames.
    rust_server.start_tcp_server()
    # Launch the background task to continuously update video frames.
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
    return HTMLResponse(content=DASHBOARD_HTML)


# New GET endpoint to provide extra meta data.
@app.get("/meta_data")
async def meta_data():
    default_payload = {"is_active": False, "active_prompt": ""}
    instructions = robot_brain.process_meta(default_payload)
    observations = getattr(robot_brain, "observations", ["No observations available"])
    pathfinding = getattr(robot_brain, "pathfinding_thoughts", "No pathfinding data")
    return {
        "meta_payload": default_payload,
        "meta_response": instructions,
        "observations": observations,
        "pathfinding": pathfinding,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }


@app.post("/meta")
async def get_meta(payload: dict):
    """
    Processes the meta payload using the ARST brain.

    Expected payload JSON:
    {
        "is_active": bool,
        "active_prompt": string
    }

    Returns a JSON response with:
        - instructions: list of instructions for the robot.
        - timestamp: when the response was generated.
        - observations: robot's current observations.
        - pathfinding: current pathfinding thoughts.
    """
    instructions = robot_brain.process_meta(payload)
    # Simulated additional data from the robot brain.
    observations = getattr(robot_brain, "observations", ["No observations available"])
    pathfinding = getattr(robot_brain, "pathfinding_thoughts", "No pathfinding data")
    return {
        "instructions": instructions,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "observations": observations,
        "pathfinding": pathfinding,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
