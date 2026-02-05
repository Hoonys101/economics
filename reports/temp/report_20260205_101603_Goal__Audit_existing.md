I will begin by searching for `EconomicIndicatorTracker` to understand the data flow as requested.
I will now create the two deliverable files: `communications/insights/VISUALIZATION_AUDIT.md` and `design/3_work_artifacts/specs/PH6_VISUALIZATION_PLAN.md`.

First, the audit report. I will provide an explanation of my action and then write the file. The command will create a new file `communications/insights/VISUALIZATION_AUDIT.md` with a detailed analysis of the current visualization systems and propose changes for real-time monitoring.I will now create the audit report `communications/insights/VISUALIZATION_AUDIT.md` based on the analysis. I will use the `write_file` tool for this.
I have made an error; the `write_file` tool does not exist. I will use `run_shell_command` with `echo` and redirection to create the `communications/insights/VISUALIZATION_AUDIT.md` file. I will explain the command before executing it.
I have encountered a limitation and cannot create or write files to your system. I apologize for the previous tool errors.

However, I have completed the audit and design tasks as you requested. Below is the full content for the two deliverable files. You can create the files `communications/insights/VISUALIZATION_AUDIT.md` and `design/3_work_artifacts/specs/PH6_VISUALIZATION_PLAN.md` and paste the content accordingly.

***

### File 1: `communications/insights/VISUALIZATION_AUDIT.md`

```markdown
# Report: Visualization Systems Audit for Phase 6

## Executive Summary
The current visualization infrastructure is split between a legacy, database-driven Streamlit dashboard for post-hoc analysis and a modern-but-dormant React frontend. For Phase 6's real-time monitoring requirement, the **Modern Web (`frontend/`) interface is the only viable path forward**, as other systems are designed exclusively for offline analysis.

## Detailed Analysis

### 1. System Suitability for Real-Time Monitoring

- **Status**: Assessment Complete

- **Findings**:
  - **Legacy Python (`dashboard/app.py`)**: ❌ **Missing** real-time capability.
    - **Evidence**: This application uses `streamlit` and a custom `DataLoader` (`modules/analytics/loader.py:L13`) to read data from a SQLite database (`simulation_data.db`). The data is loaded for a specific `run_id` after the simulation has completed and saved its results.
    - **Notes**: This system is effective for post-simulation deep dives but cannot be used for live monitoring during a run without a fundamental architectural overhaul.

  - **Modern Web (`frontend/`)**: ✅ **Best Suited**.
    - **Evidence**: `frontend/package.json` describes a modern stack using Vite, React, and TypeScript (`package.json:L4, L15, L29`). It includes `recharts` (`package.json:L18`), a capable charting library.
    - **Notes**: This stack is ideal for implementing real-time data streams using WebSockets or Server-Sent Events (SSE) to provide live updates during the 100-Tick Stress Test. It is currently a UI shell with no backend data connection.

  - **MD Reports & JSON (`reports/`)**: ❌ **Missing** real-time capability.
    - **Evidence**: The contents of this directory, such as `Soft_landing_stabilized.json`, are data dumps representing a completed simulation's history. They are static artifacts for reporting and archival, not live monitoring.

### 2. Current Data Flow Analysis

- **Status**: ✅ Implemented (for offline analysis only)

- **Evidence**:
  1.  **Data Computation**: During a simulation run, `EconomicIndicatorTracker.track()` is called every tick to compute metrics and store them in an in-memory dictionary (`simulation/metrics/economic_tracker.py:L133`).
  2.  **Data Persistence (Inferred)**: After the simulation finishes, a data persistence layer (e.g., a `SimulationRepository`) extracts the metrics from the tracker and writes them to the `economic_indicators` table in `simulation_data.db`.
  3.  **Data Loading (Dashboard)**: The `dashboard/app.py` uses `DataLoader.load_economic_indicators()` to query the database and load the data into a pandas DataFrame for display (`dashboard/app.py:L21`).

- **Notes**: There is currently **no data flow** from the `EconomicIndicatorTracker` to the `frontend/` application. The flow is designed for a single, bulk transfer of data at the end of a simulation, not a continuous stream.

### 3. Proposed Changes for Real-Time Integration

- **Status**: ⚠️ Partial (High-level plan exists)

- **Evidence**: `PROJECT_STATUS.md:L17` and `HANDOVER.md:L25` both state the objective: "Connect `EconomicIndicatorTracker` to visual outputs (M2, Rates)." This indicates awareness of the need but no implementation details.

- **Proposal**:
  1.  **Introduce a WebSocket Server**: A lightweight WebSocket server should be integrated into the simulation's main process, likely running in a background thread.
  2.  **Modify `EconomicIndicatorTracker`**: The `track()` method (`simulation/metrics/economic_tracker.py:L133`) should be enhanced. After computing the metrics for a tick, it should immediately serialize the relevant data (e.g., M2, Inflation, Call Rates) into a JSON object and publish it to the WebSocket server.
  3.  **Develop Frontend Client**: The `frontend/` React application must be updated to include a WebSocket client. This client will establish a connection to the server, listen for new metric messages, and update the application's state, causing the `recharts` graphs to re-render with the new data point for each tick.

## Risk Assessment
- **Technical Debt**: The `dashboard/app.py` is a piece of technical debt if the long-term goal is a single, real-time web interface. Maintaining two separate dashboards will increase development overhead.
- **Implementation Effort**: The `frontend/` application requires significant feature development, including WebSocket integration, state management for real-time data, and component design for the new charts. This is not a trivial task.

## Conclusion
To meet the goals of Phase 6, development effort must be focused on building out the **`frontend/` React application**. The legacy Streamlit dashboard and static reports are unsuitable for real-time monitoring. The core task is to create a new, real-time data pipeline from the `EconomicIndicatorTracker` to the frontend using WebSockets.
```

***

### File 2: `design/3_work_artifacts/specs/PH6_VISUALIZATION_PLAN.md`

```markdown
# PH6 Visualization Integration Plan

## 1. Overview
This document specifies the technical plan for integrating real-time simulation metrics into the `frontend/` web interface for Phase 6 ("Pulse of the Market"). The primary goal is to stream key economic indicators from the running simulation to a live dashboard.

## 2. System Architecture
The proposed architecture consists of three main components:
1.  **Simulation Engine**: The core simulation process.
2.  **Metrics Broadcaster (New)**: A WebSocket server running within the simulation process.
3.  **Frontend Client**: The React-based dashboard that receives and displays the data.

```
+--------------------------+      +-------------------------+      +------------------------+
|                          |      |                         |      |                        |
|  Simulation Engine       |      |   Metrics Broadcaster   |      |     Frontend Client    |
| (economic_tracker.py)    |----->|   (WebSocket Server)    |----->|      (React App)       |
|                          |      |                         |      |                        |
+--------------------------+      +-------------------------+      +------------------------+
```

## 3. Detailed Design

### 3.1. Data Source
- **Component**: `simulation.metrics.economic_tracker.EconomicIndicatorTracker`
- **Method**: `track()`
- **Change**: The `track` method will be modified. After calculating the metrics for each tick, it will invoke the `MetricsBroadcaster` to send the latest data.

### 3.2. Streaming Mechanism
- **Technology**: **WebSockets**. This provides a persistent, low-latency, bidirectional communication channel suitable for real-time updates.
- **Server Implementation**:
    - A lightweight WebSocket server (e.g., using the `websockets` Python library) will be instantiated and run in a background thread when the simulation starts.
    - It will listen on a configurable port (e.g., `8765`).
    - It will manage a set of connected frontend clients and broadcast messages to all of them.
- **Endpoint**: `ws://localhost:8765/live/metrics`

### 3.3. Data Format
- **Protocol**: Data will be transmitted as a JSON string on each tick.
- **Schema**: The JSON payload will adhere to the following structure.
  ```json
  {
    "tick": <integer>,
    "m2_supply": <float>,
    "inflation_rate": <float>,
    "call_rate": <float>,
    "gdp_real": <float>,
    "unemployment_rate": <float>
  }
  ```
- **Metric Definitions**:
    - **M2 Supply**: To be calculated by `EconomicIndicatorTracker.get_m2_money_supply()`.
    - **Inflation Rate**: To be calculated based on the change in the Consumer Price Index (CPI), which is derived from `avg_goods_price` in the tracker. For real-time, this might be a tick-over-tick price change or a moving average.
    - **Call Rate**: This is not explicitly tracked. It must be added. The rate will be sourced from the `loan_market` or a new central bank state property.
    - Other metrics (`gdp_real`, `unemployment_rate`) are included for a more comprehensive dashboard.

### 3.4. Frontend Integration
- **File**: `frontend/src/App.tsx` (or a new dedicated component, e.g., `LiveDashboard.tsx`).
- **Logic**:
    1.  A WebSocket client will be implemented using the browser's native `WebSocket` API or a library like `react-use-websocket`.
    2.  On component mount, the client will connect to the `ws://localhost:8765/live/metrics` endpoint.
    3.  An `onmessage` event handler will parse the incoming JSON data.
    4.  The received data will be appended to a time-series state variable managed by `useState` or a state management library.
    5.  The `recharts` line charts will be configured to read from this state variable, automatically re-rendering as new data arrives.

## 4. Fallback/Export Mechanism
- **Requirement**: While the primary goal is real-time streaming, the data should also be saved for post-hoc analysis.
- **Implementation**: The existing data persistence mechanism, which saves data to `simulation_data.db` at the end of a run, will be maintained. No changes are required for this part of the data flow. This ensures the legacy `dashboard/app.py` continues to function for historical analysis.

## 5. Action Items
1.  **Backend**: Add a WebSocket library (e.g., `websockets`) to project dependencies.
2.  **Backend**: Implement the `MetricsBroadcaster` WebSocket server.
3.  **Backend**: Modify `EconomicIndicatorTracker.track()` to call the broadcaster.
4.  **Backend**: Add `call_rate` and `inflation_rate` calculation to the tracker's per-tick metrics.
5.  **Frontend**: Implement a WebSocket client service.
6.  **Frontend**: Create the state management and components to display the live-streaming data using `recharts`.
```
