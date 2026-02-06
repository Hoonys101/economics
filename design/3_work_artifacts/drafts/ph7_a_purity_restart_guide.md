# Mission Guide: PH7-A-PURITY - Enhanced Domain Purity Reforms

## 1. Context & Objectives
The previous implementation of TD-255/256 hit a bottleneck regarding inventory audit violations. This mission restarts the process with a focus on resolving those specific violations and enforcing the `IInventoryHandler` protocol.

**Core Goal**: Eliminate all direct `.inventory` access across the simulation engine, ensuring all state changes are transactional and audited.

## 2. Reference Context
- **Primary Spec**: `design/3_work_artifacts/specs/spec_combined_purity_reforms.md`
- **Audit Report**: `reports/temp/report_20260206_193948_Identify_all_remaini.md` (Read this FIRST)
- **Merged Base**: `main` (Includes `BaseAgent` memory fix and Watchtower lock fix).

## 3. Handling the "27 Violations"
Based on the previous run, ~27 "violations" were found. These must be handled as follows:

| Category | Finding | Jules's Action |
| :--- | :--- | :--- |
| **Pure Data** | Accessing `EconStateDTO.inventory` | **SAFE**. DTOs are immutable read-only snapshots. No change needed. |
| **Agnostic Metadata** | Accessing `inventory_quality` or `inventory_last_sale_tick` | **REFAC**. Move these into the `IInventoryHandler` protocol or a related metadata handler. |
| **Persistence** | `agent_data['inventory']` in `persistence_manager` | **SAFE**. This is serialization, not business logic. |
| **External Logic** | `market.py` or `residence.py` accessing `.inventory` | **VIOLATION**. Must be refactored to use `get_quantity`, `add_item`, or `remove_item` via the Protocol. |

## 4. Implementation Roadmap

### Phase 1: Protocol Deployment (TD-256)
- Standardize `IInventoryHandler` in `modules/simulation/api.py` (ensure `quality` is supported).
- Implement in `BaseAgent`, `Firm`, and `Household`.
- **CRITICAL**: Remove the `inventory` property from `BaseAgent` to force compile-time/runtime errors at violation sites.

### Phase 2: Systematic Refactoring
- Refactor `Registry.py`, `SettlementSystem.py`, and all Market classes.
- Use the Gemini Audit Report as a checklist.

### Phase 3: Saga Purity (TD-255)
- Implement `HouseholdSnapshotDTO` in `HousingTransactionSagaHandler`.
- Ensure the Saga *never* touches the live agent object after initiation.

## 5. Verification
- `python scripts/trace_leak.py`: Must remain 0.0000% leakage.
- `python scripts/audit_inventory_access.py`: Must yield 0 "Violations" (excluding documented Safe cases).
- `pytest tests/integration/test_inventory_purity.py`: (Create this test) Verify isolation.

---
**"Precision is the only cure for technical debt."**
