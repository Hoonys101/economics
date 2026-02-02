# TD-065 Housing Planner Implementation

## Phenomenon
The housing market logic was fragmented ("orphaned"), with decision-making split between `DecisionUnit` (System 2) and `HousingSystem`. Agents often failed to execute housing transactions because:
1.  They couldn't correctly signal intent to the market (missing `loan_application` in Orders).
2.  The `HousingTransactionHandler` expected specific DTO structures (`LoanInfoDTO`) but received mismatched types or was invoked with incorrect arguments.
3.  The `EscrowAgent` was missing from the agent registry during critical transaction phases, causing settlement failures.

## Cause
1.  **Orphaned Logic:** `HouseholdSystem2Planner` calculated NPV but didn't generate actionable Orders with mortgage intent. `HousingTransactionHandler` required a valid `loan_id` which wasn't being propagated.
2.  **State Fracture:** The simulation state (`SimulationState`) and world state (`WorldState`) were desynchronized in terms of agent lists. Specifically, `escrow_agent` was instantiated but not added to the `state.agents` map passed to the `TransactionProcessor`, leading to "Escrow Agent not found" errors during atomic settlement.
3.  **DTO Mismatch:** `HousingTransactionHandler` accessed `new_loan_dto` as an object (`.loan_id`), but `Bank.grant_loan` returned a `TypedDict`, causing `AttributeError`.

## Solution
1.  **Centralized HousingPlanner:** Implemented `HousingPlanner` in `modules/market/`. It encapsulates all Buy/Rent/Stay logic, including affordability checks and NPV-like scoring.
2.  **DTO Standardization:** Defined `HousingOfferRequestDTO`, `HousingDecisionDTO`, and `LoanApplicationDTO`. Updated `HousingTransactionHandler` to correctly parse `LoanInfoDTO` (TypedDict).
3.  **Escrow Integration:** Added `escrow_agent` to `SimulationState` DTO and ensured it is registered in `state.agents` within `TickOrchestrator` and `AgentLifecycleManager`.
4.  **Verification:** Created `scripts/verify_housing_transaction_integrity.py` which successfully simulates a wealthy homeless buyer purchasing a home, verifying mortgage creation and ownership transfer.

## Lesson Learned
*   **State Integrity is Paramount:** When using DTOs (`SimulationState`) to pass state to systems, ensure *all* auxiliary agents (like Escrow, Central Bank) are explicitly included. Relying on implicit availability in `world_state` is fragile.
*   **TypedDict vs Dataclass:** Be consistent. `LoanInfoDTO` is a `TypedDict` but was accessed like a dataclass. Static analysis or stricter typing in handlers prevents runtime crashes.
*   **Component Isolation:** Moving housing logic to `HousingPlanner` (stateless) made it significantly easier to test and verify without running the entire `DecisionEngine` cognitive stack.
