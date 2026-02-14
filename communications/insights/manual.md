# Architectural Insights
1. **Global `sys.modules` Patching in Tests is Harmful:** Manually modifying `sys.modules` in a test file (e.g., `sys.modules["websockets"] = Mock()`) affects the entire test process, including subsequent tests that rely on the real module. This leads to confusing failures like `ModuleNotFoundError` for submodules because the Mock object is not a package.
2. **Conditional Mocking in `conftest.py` is Robust:** Centralizing mocks for optional dependencies in `conftest.py` ensures that tests can run in minimal environments while still allowing integration tests to use real libraries when available. Adding `mock.__path__ = []` is crucial for mimicking packages to support submodule imports.

# Test Evidence
```
tests/unit/dashboard/test_socket_manager.py::TestSocketManager::test_audit_logs PASSED [ 16%]
tests/unit/dashboard/test_socket_manager.py::TestSocketManager::test_initialization PASSED [ 33%]
tests/unit/dashboard/test_socket_manager.py::TestSocketManager::test_send_command PASSED [ 50%]
tests/unit/dashboard/test_socket_manager.py::TestSocketManager::test_telemetry_handling PASSED [ 66%]
tests/integration/test_server_integration.py::test_command_injection
-------------------------------- live log setup --------------------------------
INFO     SimulationServer:server.py:27 SimulationServer thread started on localhost:38315
INFO     websockets.server:server.py:341 server listening on 127.0.0.1:38315
INFO     websockets.server:server.py:341 server listening on [::1]:38315
INFO     SimulationServer:server.py:35 WebSocket server running...
-------------------------------- live log call ---------------------------------
INFO     websockets.server:server.py:531 connection open
INFO     SimulationServer:server.py:43 Client connected: ('::1', 59268, 0, 0)
INFO     SimulationServer:server.py:58 Client disconnected: ('::1', 59268, 0, 0)
PASSED                                                                   [ 83%]
tests/integration/test_server_integration.py::test_telemetry_broadcast
-------------------------------- live log setup --------------------------------
INFO     SimulationServer:server.py:27 SimulationServer thread started on localhost:60639
INFO     websockets.server:server.py:341 server listening on [::1]:60639
INFO     websockets.server:server.py:341 server listening on 127.0.0.1:60639
INFO     SimulationServer:server.py:35 WebSocket server running...
-------------------------------- live log call ---------------------------------
INFO     websockets.server:server.py:531 connection open
INFO     SimulationServer:server.py:43 Client connected: ('::1', 48328, 0, 0)
INFO     SimulationServer:server.py:58 Client disconnected: ('::1', 48328, 0, 0)
PASSED                                                                   [100%]

============================== 6 passed in 2.96s ===============================
```
