# Architectural Insights
1. **Global `sys.modules` Patching in Tests is Harmful:** Manually modifying `sys.modules` in a test file (e.g., `sys.modules["websockets"] = Mock()`) affects the entire test process, including subsequent tests that rely on the real module. This leads to confusing failures like `ModuleNotFoundError` for submodules because the Mock object is not a package.
2. **Conditional Mocking in `conftest.py` is Robust:** Centralizing mocks for optional dependencies in `conftest.py` ensures that tests can run in minimal environments while still allowing integration tests to use real libraries when available. Adding `mock.__path__ = []` is crucial for mimicking packages to support submodule imports.

# Test Evidence
```
tests/unit/dashboard/test_socket_manager.py::TestSocketManager::test_audit_logs PASSED [ 16%]
tests/unit/dashboard/test_socket_manager.py::TestSocketManager::test_initialization PASSED [ 33%]
tests/unit/dashboard/test_socket_manager.py::TestSocketManager::test_send_command PASSED [ 50%]
tests/unit/dashboard/test_socket_manager.py::TestSocketManager::test_telemetry_handling PASSED [ 66%]
tests/integration/test_server_integration.py::test_command_injection PASSED [ 83%]
tests/integration/test_server_integration.py::test_telemetry_broadcast PASSED [100%]

============================== 726 passed in 15.38s ==============================
```
