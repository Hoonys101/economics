# Cockpit 2.0 FE-1: Foundation Insight Report

## Architectural Insights
1. **Dual-WebSocket Architecture**: Implemented a separation of concerns with two distinct WebSocket channels:
   - `/ws/live`: A read-only stream for high-frequency `WatchtowerSnapshotDTO` updates.
   - `/ws/command`: A write-only command channel for `CockpitCommand` dispatch, protected by authentication.
   This design prevents command traffic from blocking or being blocked by the telemetry stream.

2. **DTO Parity**: strict TypeScript interfaces (`frontend/src/types/watchtower.ts`, `frontend/src/types/cockpit.ts`) were created to mirror the Python `dataclass` definitions. This ensures type safety and autocompletion in the frontend, reducing integration bugs.

3. **Authentication Update**: The backend (`server.py`) was modified to accept the `X-GOD-MODE-TOKEN` via a query parameter (`?token=...`) in addition to the HTTP header. This was necessary because standard browser `WebSocket` APIs do not support setting custom headers during the connection handshake.

4. **Component Architecture**:
   - `HUD`: A pure presentational component consuming `WatchtowerSnapshotDTO`.
   - `GodBar`: A control component dispatching commands via `useCockpit`.
   - `useCockpit`: A custom hook encapsulating the WebSocket logic (connection, reconnection, state management), providing a clean API to the UI components.

## Test Evidence

### Backend Authentication Verification
The following `pytest` output demonstrates that `server.py` correctly handles the new query parameter authentication method and rejects invalid tokens.

```
$ python -m pytest tests/test_server_auth.py
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
plugins: asyncio-0.24.0, anyio-4.8.0, mock-3.14.0
collected 3 items

tests/test_server_auth.py::test_websocket_auth_query_param
-------------------------------- live log call ---------------------------------
INFO     server:server.py:137 Cockpit connected to /ws/command
INFO     server:server.py:160 Cockpit disconnected from /ws/command
PASSED                                                                   [ 33%]
tests/test_server_auth.py::test_websocket_auth_header
-------------------------------- live log call ---------------------------------
INFO     server:server.py:137 Cockpit connected to /ws/command
INFO     server:server.py:160 Cockpit disconnected from /ws/command
PASSED                                                                   [ 66%]
tests/test_server_auth.py::test_websocket_auth_failure
-------------------------------- live log call ---------------------------------
WARNING  server:server.py:132 Unauthorized connection attempt to /ws/command. Token provided: Yes
PASSED                                                                   [100%]

============================== 3 passed in 0.60s ===============================
```

### Frontend Build Verification
The frontend successfully compiles with TypeScript validation.

```
$ cd frontend && npm run build
> frontend@0.0.0 build
> tsc -b && vite build

vite v7.3.0 building client environment for production...
transforming...
✓ 1706 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.46 kB │ gzip:  0.29 kB
dist/assets/index-CTiKDbku.css   20.52 kB │ gzip:  5.87 kB
dist/assets/index-tx8Pe1wG.js   205.91 kB │ gzip: 64.90 kB
✓ built in 2.84s
```
