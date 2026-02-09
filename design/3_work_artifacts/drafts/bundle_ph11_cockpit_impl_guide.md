# Mission Guide: Phase 11 The Simulation Cockpit (Active Control)

## 1. Objectives
- Implement **Active Governance** via a write-only Command Stream.
- Enable **Hot-Swapping** of `SimulationConfig` parameters (Interest Rates, Taxes) via WebSocket.
- Build the **HUD** for real-time M2 Integrity monitoring.

## 2. Core Components
- **Command API**: `modules/governance/cockpit/api.py` [NEW]
- **Services**: `simulation/orchestration/command_service.py` [NEW]
- **Engine Bridge**: `simulation/engine.py` (Add command queue processing)
- **Technical Specification**: [draft_133154_Generate_a_Technical_Specifica.md](file:///c:/coding/economics/design/3_work_artifacts/drafts/draft_133154_Generate_a_Technical_Specifica.md)

## 3. Implementation Roadmap
1.  **Define Command DTOs**: Create `CockpitCommand` and payloads (e.g., `SetBaseRatePayload`) in `modules/governance/cockpit/api.py`.
2.  **Implement `CommandService`**:
    - Handle incoming WebSocket commands.
    - Validate payloads (e.g., rates within 0-20%).
    - Enqueue to `simulation.command_queue`.
3.  **Modify `Simulation.tick()`**:
    - Before logic runs, process all pending commands in the queue.
    - Execute `PAUSE`, `RESUME`, and `STEP`.
    - Apply `SET_BASE_RATE` directly to `config` and `central_bank`.
4.  **Frontend Prototype**:
    - Update `watchtower/` (Next.js) or Streamlit to connect to `/ws/command`.
    - Implement the **M2 Leak Integrity Light** (Red if leak != 0).
    - Add the **Rate Slider** linked to the WebSocket command.

## 4. Verification
- [ ] `test_simulation_engine_processes_pause`
- [ ] `test_simulation_engine_applies_config_change`
- [ ] E2E: Drag rate slider in UI -> Verify `simulation.config.economy.base_interest_rate` updates instantly.
