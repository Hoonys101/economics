import asyncio
import logging
import signal
import sys
import os
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from utils.simulation_builder import create_simulation
from simulation.orchestration.dashboard_service import DashboardService
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

# Global State
sim = None
dashboard_service = None
background_task = None
is_running = False

def handle_signal(sig, frame):
    """
    Handle termination signals to ensure the loop stops.
    Uvicorn will handle the main shutdown, but this ensures our loop flag is cleared.
    """
    global is_running
    logger.info(f"Received signal {sig}. Initiating shutdown...")
    is_running = False

async def simulation_loop():
    global sim, is_running
    logger.info("Starting simulation loop...")
    while is_running:
        if sim:
            try:
                # Run tick in thread pool to prevent blocking the event loop
                await asyncio.to_thread(sim.run_tick)

                # Yield control to event loop
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}", exc_info=True)
                await asyncio.sleep(1.0) # Backoff
        else:
            await asyncio.sleep(1.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sim, dashboard_service, background_task, is_running

    # Startup
    logger.info("Initializing simulation...")
    try:
        # overrides can be passed here if needed
        sim = create_simulation()
        dashboard_service = DashboardService(sim)

        is_running = True
        background_task = asyncio.create_task(simulation_loop())
    except Exception as e:
        logger.critical(f"Failed to initialize simulation: {e}", exc_info=True)
        # We should probably re-raise so the server doesn't start in a broken state
        raise e

    yield

    # Shutdown
    logger.info("Shutting down simulation...")
    is_running = False
    if background_task:
        # Cancel the task to stop sleep immediately if needed, or wait for it to check flag
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass

    if sim:
        try:
            sim.finalize_simulation()
        except Exception as e:
            logger.error(f"Error during simulation finalization: {e}", exc_info=True)

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if dashboard_service:
                # Serves WatchtowerSnapshotDTO (TD-125)
                snapshot = dashboard_service.get_snapshot()
                # Use asdict to convert dataclass to dict
                data = asdict(snapshot)
                await websocket.send_json(data)

            # Throttling to Max 1Hz (1 second delay)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

@app.get("/")
def read_root():
    return {"status": "Watchtower Server Running"}

if __name__ == "__main__":
    import uvicorn
    # Register signal handlers to set the flag
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
