# Architectural Insights: Event-Driven WebSocket Broadcast

## Technical Debt & Architectural Decisions

1.  **Event-Driven vs Polling**: Transitioned `SimulationServer` from a 10Hz polling loop to an event-driven architecture using the Observer pattern. This was achieved by adding `subscribe`/`unsubscribe` methods to the `TelemetryExchange` bridge. This reduces CPU usage during idle times and ensures immediate broadcast upon simulation ticks.

2.  **Thread Safety**: The `TelemetryExchange` bridge manages data updates from the Simulation Thread (Thread A) and notifications to the Server Loop (Thread B). We utilized `asyncio.loop.call_soon_threadsafe` to safely schedule broadcast tasks on the server's event loop from the simulation thread.

3.  **Client State Management**: Initially considered monkey-patching the `websocket` object to store `last_sent_tick`, but refactored to use a dedicated `self.client_states` dictionary in `SimulationServer`. This avoids potential issues with `__slots__` optimization in the `websockets` library and provides a cleaner separation of concerns.

4.  **Race Condition Handling**: Implemented logic to handle the race condition where a client connects and receives an initial snapshot concurrently with a tick broadcast. By tracking `last_sent_tick` per client, we ensure clients receive strictly monotonically increasing ticks and no duplicates.

## Test Evidence

### Unit Tests (`tests/unit/modules/system/test_server_bridge.py`)

```
...
----------------------------------------------------------------------
Ran 3 tests in 0.120s

OK
```

### Integration Tests (`tests/integration/test_server_integration.py`)

```
tests/integration/test_server_integration.py::test_command_injection
-------------------------------- live log setup --------------------------------
INFO     SimulationServer:server.py:28 SimulationServer thread started on localhost:43739
INFO     websockets.server:server.py:341 server listening on 127.0.0.1:43739
INFO     websockets.server:server.py:341 server listening on [::1]:43739
INFO     SimulationServer:server.py:48 WebSocket server running...
-------------------------------- live log call ---------------------------------
INFO     websockets.server:server.py:531 connection open
INFO     SimulationServer:server.py:58 Client connected: ('::1', 36568, 0, 0)
INFO     SimulationServer:server.py:80 Client disconnected: ('::1', 36568, 0, 0)
PASSED                                                                   [ 50%]
tests/integration/test_server_integration.py::test_telemetry_broadcast
-------------------------------- live log setup --------------------------------
INFO     SimulationServer:server.py:28 SimulationServer thread started on localhost:34493
INFO     websockets.server:server.py:341 server listening on 127.0.0.1:34493
INFO     websockets.server:server.py:341 server listening on [::1]:34493
INFO     SimulationServer:server.py:48 WebSocket server running...
-------------------------------- live log call ---------------------------------
INFO     websockets.server:server.py:531 connection open
INFO     SimulationServer:server.py:58 Client connected: ('::1', 35414, 0, 0)
INFO     SimulationServer:server.py:80 Client disconnected: ('::1', 35414, 0, 0)
PASSED                                                                   [100%]

============================== 2 passed in 2.88s ===============================
```
