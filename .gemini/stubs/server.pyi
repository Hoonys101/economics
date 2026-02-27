from _typeshed import Incomplete
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket as WebSocket

logger: Incomplete
sim: Incomplete
dashboard_service: Incomplete
agent_service: Incomplete
background_task: Incomplete
is_running: bool
is_ready: bool

def handle_signal(sig, frame) -> None:
    """
    Handle termination signals to ensure the loop stops.
    Uvicorn will handle the main shutdown, but this ensures our loop flag is cleared.
    """
async def simulation_loop() -> None: ...
@asynccontextmanager
async def lifespan(app: FastAPI): ...

app: Incomplete

async def websocket_endpoint(websocket: WebSocket): ...
async def command_endpoint(websocket: WebSocket): ...
async def agents_websocket_endpoint(websocket: WebSocket): ...
async def get_agent_detail(agent_id: int): ...
def read_root(): ...
