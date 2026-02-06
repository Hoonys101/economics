# Technical Insight: Settlement Kernel Hardening & Saga Decoupling (TD-253)

## 1. Problem Phenomenon
The `SettlementSystem` had evolved into a "God Class", mixing low-level transactional mechanics with high-level business process management (Sagas). This created several critical issues:
*   **Coupling**: The system was tightly coupled to the Housing Market saga logic (`active_sagas`, `process_sagas`), making it difficult to refactor or test settlement logic independently.
*   **Abstraction Leaks**: The system used `hasattr` checks to inspect internal properties of agents (`wallet`, `finance`, `_econ_state`), violating encapsulation and making the system fragile to agent implementation changes.
*   **M2 Integrity Risks**: Saga handlers were manually appending `Transaction` objects to the global log to track credit expansion, bypassing central accounting and increasing the risk of M2 drift.

## 2. Root Cause Analysis
*   **Lack of dedicated orchestration**: There was no dedicated service for managing long-running transactions, so the logic "leaked" into the most convenient place (`SettlementSystem`).
*   **Legacy Agent diversity**: The system had to support multiple generations of agent implementations (Household vs Firm vs Government), leading to defensive coding (`hasattr`) instead of strict interfaces.
*   **Observability vs Action**: The distinction between *creating* money (action) and *logging* the expansion (observation) was blurred in the Saga handlers.

## 3. Solution Implementation Details
The refactoring was executed in three phases:

### Phase 1: Core Interfaces & Ledger
*   Defined `ISagaOrchestrator`, `IMonetaryLedger`, and a purified `ISettlementSystem` in `modules/finance/kernel/api.py`.
*   Implemented `MonetaryLedger` to provide a dedicated, safe API for recording credit expansion/destruction events, ensuring consistent M2 tracking.
*   Implemented `FinancialEntityAdapter` to encapsulate the legacy agent inspection logic, providing a uniform `IFinancialEntity` interface to the kernel.

### Phase 2: Orchestration Extraction
*   Created `SagaOrchestrator` (`modules/finance/sagas/orchestrator.py`) and moved all saga-related logic (`active_sagas`, `process_sagas`, `submit_saga`) out of `SettlementSystem`.
*   Updated `SimulationState`, `WorldState`, and `SimulationInitializer` to integrate the new `SagaOrchestrator` and `MonetaryLedger` as first-class citizens.
*   Updated `TickOrchestrator` and `Phase_HousingSaga` to delegate saga processing to the new orchestrator.

### Phase 3: Kernel Cleanup
*   Refactored `SettlementSystem` to remove all saga methods.
*   Updated `SettlementSystem` to use `FinancialEntityAdapter` for safe, polymorphic asset access.
*   Refactored `HousingTransactionSagaHandler` to use `MonetaryLedger` for logging, eliminating manual transaction log manipulation.

## 4. Lessons Learned & Technical Debt
*   **Interface Adoption**: The `FinancialEntityAdapter` is a powerful bridge, but ultimately agents should natively implement `IFinancialEntity` to remove the runtime overhead of adaptation.
*   **State Injection**: The dependency of `HousingTransactionSagaHandler` on the full `ISimulationState` remains a "God Object" smell. Future refactoring should inject only specific required services (e.g., `ILoanMarket`, `IPropertyRegistry`).
*   **Test Coverage**: While unit tests were updated, the integration of Sagas relies heavily on the `Phase_HousingSaga` test. Explicit integration tests for the full Saga lifecycle with the new Orchestrator would be beneficial.
