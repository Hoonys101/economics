# Server Integration & Async Dependencies Fix

## [Architectural Insights]
*   **Dependency Management**: Cleaned up `requirements.txt` to remove redundant `pytest-asyncio` entries and pinned the version to `>=0.24.0` to ensure compatibility with modern asyncio testing patterns.
*   **Async Testing Configuration**: Verified `pytest.ini` enforces `asyncio_default_fixture_loop_scope = function`, which aligns with `pytest-asyncio`'s strict mode, ensuring test isolation and preventing event loop leakage between tests.
*   **Server Integration**: The integration tests (`tests/integration/test_server_integration.py`) correctly utilize a threaded `SimulationServer` alongside async test functions. This separation (server in thread, client in async test loop) avoids event loop conflicts and correctly simulates a real network environment.

## [Test Evidence]
```
tests/integration/test_server_integration.py::test_command_injection
-------------------------------- live log setup --------------------------------
INFO     SimulationServer:server.py:27 SimulationServer thread started on localhost:53719
INFO     websockets.server:server.py:341 server listening on [::1]:53719
INFO     websockets.server:server.py:341 server listening on 127.0.0.1:53719
INFO     SimulationServer:server.py:35 WebSocket server running...
-------------------------------- live log call ---------------------------------
INFO     websockets.server:server.py:531 connection open
INFO     SimulationServer:server.py:43 Client connected: ('::1', 36988, 0, 0)
INFO     SimulationServer:server.py:58 Client disconnected: ('::1', 36988, 0, 0)
PASSED                                                                   [ 50%]
tests/integration/test_server_integration.py::test_telemetry_broadcast
-------------------------------- live log setup --------------------------------
INFO     SimulationServer:server.py:27 SimulationServer thread started on localhost:58567
INFO     websockets.server:server.py:341 server listening on [::1]:58567
INFO     websockets.server:server.py:341 server listening on 127.0.0.1:58567
INFO     SimulationServer:server.py:35 WebSocket server running...
-------------------------------- live log call ---------------------------------
INFO     websockets.server:server.py:531 connection open
INFO     SimulationServer:server.py:43 Client connected: ('::1', 40566, 0, 0)
INFO     SimulationServer:server.py:58 Client disconnected: ('::1', 40566, 0, 0)
PASSED                                                                   [100%]

============================== 2 passed in 2.95s ===============================
```
