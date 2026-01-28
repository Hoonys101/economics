# Technical Specification: TD-124 - Decomposing TransactionProcessor (Refined)

## 1. Overview & Problem Statement
The `TransactionProcessor` is a monolithic "God Class" managing financial settlement, tax fiscality, and ownership registration. This refactoring decomposes it into a modular system orchestrated by a `TransactionManager`, ensuring high cohesion, low coupling, and absolute zero-sum integrity.

## 2. Refined Architecture
The architecture is expanded into 6 specialized systems to prevent the emergence of new God Classes.

1.  **`TransactionManager` (Orchestrator)**: The intelligent router and entry point.
2.  **`CentralBank` (Minting Authority)**: Dedicated system for **non-zero-sum** transactions (`lender_of_last_resort`, `asset_liquidation`). Sole authority for money creation.
3.  **`SettlementSystem` (Financial Layer)**: Strictly handles **zero-sum** asset transfers between agents.
4.  **`TaxAgency` (Fiscal Layer)**: Calculates/collects taxes using the `SettlementSystem`.
5.  **`Registry` (Ownership Layer)**: Updates **non-financial state** only (inventory, employer_id, property ownership).
6.  **`AccountingSystem` (Ledger Layer)**: Updates agents' **internal financial ledgers** (recording revenue, expenses, capital income).
7.  **`Specialized Handlers`**: Dedicated logic for complex sagas (e.g., `InheritanceHandler`, `DividendHandler`).

## 3. Agency Interface Definitions (`api.py`)
New interfaces for `IMintingAuthority`, `IAccountingSystem`, and `ISpecializedTransactionHandler` are added to the existing definitions.

## 4. Atomic Execution Strategy (Two-Phase Commit)
1.  **Phase 1: Financial Operation (Routing)**:
    - Route to `CentralBank` for minting.
    - Route to `SpecializedHandler` for sagas.
    - Route to `SettlementSystem` for standard trades.
    - **Abort if failure occurs.**
2.  **Phase 2: State Commitment**:
    - Call `Registry.update_ownership_state`.
    - Call `AccountingSystem.update_ledgers`.

## 5. Implementation Guidance for Jules

### 5.1. Incremental Workflow
1.  **DTOs & Interfaces**: Implement in `simulation/dtos/transactions.py` and `simulation/systems/api.py`.
2.  **State Commitment Layer**: Build `Registry` and `AccountingSystem` (narrowed roles).
3.  **Financial Layer**: Implement `CentralBank` and refactor `SettlementSystem` (pure zero-sum).
4.  **Orchestration**: Implement `TransactionManager`.

### 5.2. Specialized Handlers
The logic for **Inheritance** must be encapsulated in an `InheritanceHandler`. It must handle multiple recipients correctly using `math.floor` distribution to maintain zero-sum integrity.

### 5.3. Ledgering vs. Assets
- **`SettlementSystem`** modifies `agent.assets`.
- **`AccountingSystem`** modifies `agent.finance.revenue` or `agent.capital_income_this_tick`.
- Separation ensures that financial "events" are recorded separately from the "balance" changes.

### 5.4. Verification
Run `tests/test_transaction_processor.py` (updated to use the manager) and verify money supply delta is zero for a full tick.

---
### 🚨 **Jules' Mandatory Reporting**
Logging required in `communications/insights/TD124-refined-YYYYMMDD.md`.
Focus on the routing complexity and any atomicity challenges encountered during saga handling.
