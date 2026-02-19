# Cockpit 2.0 FE-2 Insight Report

## Architectural Insights

### 1. Agent Service & DTOs
- Introduced `AgentService` in `simulation/orchestration/agent_service.py` to decouple data extraction logic from the server.
- Created `AgentBasicDTO` and `AgentDetailDTO` in `simulation/dtos/agents.py` using Pydantic for strict typing and validation.
- `AgentBasicDTO` is lightweight for scatter plot visualization (id, type, wealth, income, expense).
- `AgentDetailDTO` extends `AgentBasicDTO` with granular fields (needs, inventory, production, etc.) for the Inspector Panel.

### 2. WebSocket & API Endpoints
- Added `/ws/agents` WebSocket endpoint to stream `List[AgentBasicDTO]` periodically (throttled to 1Hz) for the Macro Canvas.
- Added `/api/v1/inspector/{agent_id}` HTTP GET endpoint for fetching detailed agent data on demand, adhering to the API Contract.
- Global `agent_service` instance manages access to simulation state.

### 3. Protocol Safety
- Used `isinstance(agent, IAgent)` checks to ensure safe access to agent properties, adhering to the "Protocol Purity" guardrail.
- Refactored `AgentService` to avoid `hasattr` checks.

### 4. Frontend Architecture
- Implemented a Sticky Layout in `App.tsx`:
    - Header (HUD): `sticky top-0 z-50`
    - Main (MacroCanvas): `flex-1 overflow-y-auto`
    - Footer (GodBar): `sticky bottom-0 z-50`
- This ensures the UI remains usable on different screen sizes and prevents the HUD from obscuring content.

## Test Evidence

### Unit Tests (`tests/unit/modules/watchtower/test_agent_service.py`)

```
tests/unit/modules/watchtower/test_agent_service.py::test_get_agents_basic_empty PASSED [ 12%]
tests/unit/modules/watchtower/test_agent_service.py::test_get_agents_basic_household PASSED [ 25%]
tests/unit/modules/watchtower/test_agent_service.py::test_get_agents_basic_firm PASSED [ 37%]
tests/unit/modules/watchtower/test_agent_service.py::test_get_agents_basic_inactive PASSED [ 50%]
tests/unit/modules/watchtower/test_agent_service.py::test_get_agents_basic_limit PASSED [ 62%]
tests/unit/modules/watchtower/test_agent_service.py::test_get_agent_detail_household PASSED [ 75%]
tests/unit/modules/watchtower/test_agent_service.py::test_get_agent_detail_firm PASSED [ 87%]
tests/unit/modules/watchtower/test_agent_service.py::test_get_agent_detail_not_found PASSED [100%]

============================== 8 passed in 0.39s ===============================
```

### Manual Verification (`verification/verify_macro_canvas.py`)

The Playwright verification script confirmed:
1.  **Navigation**: Successfully loaded `http://localhost:5173`.
2.  **WebSocket Connection**: "Agents Live" indicator appeared.
3.  **Scatter Plot**: Rendered ~20 scatter points (Wealth vs Income).
4.  **Interaction**: Clicking a point opened the Inspector Panel.
5.  **Data Fetching**: The Inspector Panel successfully fetched details via `/api/v1/inspector/{id}` (verified via `curl` as well).

```
Navigating to app...
...
Waiting for Macro Canvas...
...
Found 20 .recharts-scatter-symbol elements.
Clicking a scatter point...
Verifying Inspector Panel...
```
