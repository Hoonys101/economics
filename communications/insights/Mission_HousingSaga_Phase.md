# Mission Insight: Housing Saga Phase Integration

**Mission Key:** Mission_HousingSaga_Phase
**Date:** Current
**Author:** Jules

## 1. Technical Debt Discovered

### TD-New: Outdated Unit Tests for SettlementSystem
While implementing the `Phase_HousingSaga`, I discovered that `tests/unit/systems/test_settlement_system.py` contains test cases with outdated method signatures for `create_settlement`.
- **Implementation:** `def create_settlement(self, agent: Any, tick: int) -> LegacySettlementAccount:`
- **Test usage:** `settlement_system.create_settlement(deceased_id, cash_assets=500.0, ...)`
This discrepancy suggests that the unit tests have not been updated since the `TD-160` refactor (Atomic Settlement with Agent Object). This poses a risk where the settlement system might regress without detection in CI.

### TD-New: Phase3_Transaction Complexity
`Phase3_Transaction` currently handles multiple disparate concerns: Bank ticks, Firm transactions, Welfare, Infrastructure, Education, and previously Housing Sagas. Removing Housing Sagas helps, but it remains a "God Class" phase.

## 2. Insights & Design Decisions

### ID-001: The "Zombie Agent" Prevention Strategy
By placing `Phase_HousingSaga` immediately after `Phase_Bankruptcy` and before `Phase3_Transaction`, we enforce a strict Liveness Check barrier.
- **Problem:** Previously, a saga might try to advance a state for an agent that went bankrupt in the same tick's `Phase_Bankruptcy`.
- **Solution:** `Phase_HousingSaga` explicitly checks `is_active` for both buyer and seller. If either is inactive (e.g., liquidated), the Saga is immediately CANCELLED. This prevents the `SettlementSystem` from attempting invalid asset transfers in `Phase3_Transaction`.

### ID-002: Settlement System as Saga Orchestrator
The `SettlementSystem` is taking on the role of the Saga Orchestrator. This is appropriate as it holds the "Escrow" and "Transaction" truth. However, care must be taken not to overload it with business logic that belongs in `HousingSystem`. The current design delegates the specific step execution to `HousingTransactionSagaHandler`, keeping `SettlementSystem` focused on the lifecycle (Active -> Completed/Cancelled).

## 3. Implementation Notes
- Created `Phase_HousingSaga` in `simulation/orchestration/phases.py`.
- Modified `TickOrchestrator` to insert the new phase.
- Updated `SettlementSystem.process_sagas` to include the liveness check.
- Added comprehensive unit tests for the new phase and the liveness logic.
