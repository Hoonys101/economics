# Technical Report: Cockpit 2.0 Architectural Audit

## Executive Summary
The current Cockpit integration relies on a 1Hz WebSocket throttle for telemetry and a JSON-based command pipeline. While functional, the architecture exhibits high coupling between telemetry generation and simulation state, lacks strict boundary validation (relying on `asdict`), and contains potential performance bottlenecks in the `DashboardService` due to on-the-fly indicator calculations.

## Detailed Analysis

### 1. Data Inventory (WatchtowerSnapshotDTO)
- **Status**: ✅ Implemented
- **Evidence**: `simulation/dtos/watchtower.py`
- **Fields**:
  - `integrity`: `m2_leak` (Pennies), `fps` (Simulation speed).
  - `macro`: `gdp`, `cpi`, `unemploy`, `gini`.
  - `finance`: `rates` (base, call, loan, savings), `supply` (M0-M2, velocity).
  - `politics`: `approval` (total/low/mid/high breakdown), `status` (ruling party), `fiscal` (revenue, welfare, debt).
  - `population`: `distribution` (Q1-Q5 wealth), `active_count`, `metrics` (birth/death rates).

### 2. User Interactions (CockpitCommand)
- **Status**: ✅ Implemented
- **Evidence**: `modules/governance/cockpit/api.py`
- **Commands**:
  - `PAUSE` / `RESUME` / `STEP`: Core simulation lifecycle control.
  - `SET_BASE_RATE`: Monetary policy adjustment.
  - `SET_TAX_RATE`: Fiscal policy adjustment (Corporate/Income).
- **Processing**: Commands are enqueued via `sim.command_service.enqueue_command` and mapped to `GodCommandDTO` for execution in the tick loop.

### 3. Technical Contract Analysis
- **Protocol**: WebSocket JSON exchange.
- **Brittleness**:
  - **Serialization**: `server.py:L114` uses `asdict(snapshot)` which lacks schema enforcement and requires `json.dumps` fallback for non-serializable mocks.
  - **Validation**: `server.py:L142-152` parses commands without Pydantic/Validator, making the backend vulnerable to malformed payloads.
- **Bottlenecks**:
  - **Blocking UI**: `DashboardService.get_snapshot()` is called within the `async` loop without `to_thread`, despite performing database/repo lookups (attrition/birth counts) and calculations (`_calculate_m2_leak`).
  - **State Coupling**: Telemetry depends on `gov.approval_rating` and `state.markets`, making it fragile to model changes.

## Risk Assessment
- **TD-UI-DTO-PURITY**: Manual mapping to dicts creates technical debt and prevents automated TypeScript client generation.
- **Performance Drift**: As population grows, on-the-fly Gini and M2 leak calculations in the telemetry loop will degrade WebSocket responsiveness.

## Conclusion
The Cockpit 2.0 architecture requires transition to a Pydantic-based contract for both telemetry and commands. Moving telemetry generation to a background task or using a cached state in `DashboardService` is critical to prevent event-loop starvation.

---

### 📂 Insight Report File Contents
**Path**: `communications/insights/spec-cockpit-redesign.md`

```markdown
# Architectural Insight: Cockpit 2.0 Redesign

## 1. Architectural Insights
- **Telemetry Bottleneck**: `DashboardService.get_snapshot()` performs heavy I/O and calculations (M2 leak, demographics) on the event loop thread. 
- **Validation Gap**: Commands are accepted as raw dicts and converted to dataclasses manually, bypassing schema validation.
- **DTO Coupling**: `WatchtowerSnapshotDTO` is tightly bound to internal simulation models, complicating backend refactoring.

## 2. Hardened API Proposal (Pydantic/TypeScript)
- **Hardened Contract**: Implement `Pydantic` models for `WatchtowerSnapshot` to enable automatic JSON schema generation and frontend type-safety.
- **Command Discriminated Union**: Define `CockpitCommand` as a Union of specific command schemas (e.g., `SetBaseRateCommand`) to ensure payload integrity.

## 3. UX Enhancing Features
- **TPS Slider**: Dynamic control of simulation speed (Ticks Per Second).
- **Agent Inspector**: WebSocket endpoint for fetching granular state of a specific `AgentID` upon selection.
- **Scenario Injection**: Ability to trigger pre-defined `StressScenarioConfig` events from the UI.

## 4. Test Evidence
Existing integration tests for Cockpit command processing pass, but unit tests for transaction handlers show regressions in fiscal logging.

```text
tests/integration/test_cockpit_integration.py::test_simulation_processes_pause_resume PASSED
tests/integration/test_cockpit_integration.py::test_simulation_processes_set_base_rate PASSED
tests/integration/test_cockpit_integration.py::test_simulation_processes_set_tax_rate PASSED

FAILURES:
tests/unit/test_transaction_handlers.py::TestGoodsTransactionHandler::test_goods_success FAILED
E   AssertionError: Expected 'record_revenue' to have been called once. Called 0 times.
```
```