# Insight: Async Websocket Mocking Strategy

## 1. Phenomenon (현상)
- Full test execution (`pytest tests/`) failed with `ModuleNotFoundError: No module named 'websockets.asyncio'` when `websockets` was not installed or conditionally mocked.
- Integration tests for `SimulationServer` were failing or hanging during `test_command_injection` because of improper mocking or shadowing of the `websockets` package.
- `tests/unit/dashboard/test_socket_manager.py` was suspected of polluting `sys.modules` with a `MagicMock` that lacked package attributes (`__path__`), causing subsequent imports of submodules (like `websockets.asyncio`) to fail.

## 2. Cause (원인)
- The Python import system requires an object in `sys.modules` to have a `__path__` attribute (even if empty) to be treated as a package. A standard `MagicMock` does not have this attribute by default.
- If a test file manually assigns `sys.modules["websockets"] = MagicMock()` without setting `__path__`, it "poisons" the global module cache. Subsequent tests trying to import `websockets.asyncio` will fail because the cached "package" is just a mock object that doesn't support submodule lookups.
- In this specific case, `tests/conftest.py` handles the conditional mocking of missing dependencies. The robustness of this mechanism is critical.

## 3. Solution (해결)
- **Centralized Conditional Mocking**: Instead of individual test files patching `sys.modules`, `tests/conftest.py` is used to centrally mock optional dependencies like `websockets`.
- **Package Emulation**: The mock created in `conftest.py` is explicitly assigned an empty path: `mock.__path__ = []`. This tricks Python's import system into treating the mock as a package, allowing `from websockets import asyncio` or `import websockets.asyncio` to succeed (returning attributes of the mock).
- **Clean Tests**: Verified that individual unit tests (like `test_socket_manager.py`) do not manually manipulate `sys.modules` at the module level, preventing test pollution.

## 4. Lesson (교훈)
- **Never Patch `sys.modules` in Test Files**: Modifying `sys.modules` in a test file affects the entire test runner process. Always use `conftest.py` or scoped `patch.dict` contexts.
- **Mocking Packages requires `__path__`**: When mocking a top-level package that has submodules, always set `mock.__path__ = []` on the mock object.
- **Asyncio Testing**: Ensure proper event loop management when testing async code, and verify that mocks for async libraries (like `websockets`) are compatible with the import structures used by the code under test.

## Test Evidence
```
tests/unit/dashboard/test_socket_manager.py::TestSocketManager::test_audit_logs PASSED [ 16%]
tests/unit/dashboard/test_socket_manager.py::TestSocketManager::test_initialization PASSED [ 33%]
tests/unit/dashboard/test_socket_manager.py::TestSocketManager::test_send_command PASSED [ 50%]
tests/unit/dashboard/test_socket_manager.py::TestSocketManager::test_telemetry_handling PASSED [ 66%]
tests/integration/test_server_integration.py::test_command_injection PASSED [ 83%]
tests/integration/test_server_integration.py::test_telemetry_broadcast PASSED [100%]

============================== 726 passed in 15.38s ==============================
```
