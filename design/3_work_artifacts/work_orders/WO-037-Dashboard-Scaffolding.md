# Work Order: WO-037 - Dashboard Scaffolding (The Cockpit)

## 1. Background
The simulation has reached a level of complexity (Phase 20) where code-level variable tuning is no longer efficient. To solve the "visibility" and "control" issues, we are introducing a **Simulation Cockpit** using Streamlit. This will serve as a "God Mode" interface for real-time interaction.

## 2. Objective
Establish the infrastructure for a Python-based Web Dashboard (Streamlit) that connects to the simulation engine, allowing real-time parameter adjustment and data visualization.

## 3. Scope
- **Tech Stack**: `streamlit`, `pandas`, `altair`/`plotly`.
- **Directory**: `dashboard/` (New root level directory).
- **Core Components**:
    1.  **Launcher**: `dashboard/app.py` (Entry point).
    2.  **Controller**: Sidebar with sliders for Global Config (Tax, Interest Rate).
    3.  **Visualization**: Basic time-series plots (GDP, Population).
    4.  **Integration**: Adapting `engine.py` to run in a thread or step-by-step mode compatible with Streamlit's rerun model.

## 4. Tasks (Step-by-Step)
1.  **Dependency Setup**: Add `streamlit` to `requirements.txt` (or install command).
2.  **Scaffolding**: Create `dashboard/` folder and `dashboard/app.py`.
3.  **Engine Interface**: Create `simulation/interface/dashboard_connector.py` to bridge pure Engine and Streamlit.
    - Needs functions to: `initialize_simulation()`, `run_step()`, `get_current_state()`.
4.  **UI Layout Implementation**:
    - Sidebar: "Control Panel" (Slider for `TAX_RATE`, `BASE_INTEREST_RATE`).
    - Main Area: "Live Monitor" (Placeholder charts for `tracker` data).
5.  **Verification**: Ensure the webpage loads and clicking "Run 1 Tick" updates the charts.

## 5. Deliverables
- `dashboard/` directory with working `app.py`.
- `simulation/interface/dashboard_connector.py`.
- Updated `requirements.txt`.
- Screenshot/Confirmation of running Dashboard.
