# Spec: TD-160 Legacy Settlement Protocol

## 1. Executive Summary
This document specifies the design for the **Legacy Settlement Protocol**, a transaction-safe system to resolve an agent's estate upon death. It replaces the current direct asset transfer mechanism, which is non-atomic and causes data corruption (TD-160). The protocol will leverage a new `SettlementSystem` to guarantee zero-sum integrity of assets during inheritance.

## 2. Problem Statement
The existing inheritance process directly transfers assets from the deceased agent to their heir. If any part of this multi-step process fails (e.g., due to system errors or concurrent modifications), assets can be lost from the simulation, violating the zero-sum principle. This is a **CRITICAL** integrity risk.

## 3. Proposed Solution: The SettlementSystem

### 3.1. Core Concept
Upon an agent's death, all their assets will be transferred to a temporary, isolated `LegacySettlementAccount`. This account acts as an escrow. The `SettlementSystem` will then perform all calculations and transfers *from* this account to the designated heirs and creditors (e.g., government for inheritance tax). This ensures the original agent's accounts are closed cleanly and all subsequent transactions are managed atomically.

### 3.2. Protocol Flow
1.  **Death Event Trigger**: The `PopulationManager` detects an agent's death.
2.  **Freeze Accounts**: The deceased agent's accounts (`cash`, `stocks`, `bonds`, etc.) are frozen. No further transactions are permitted.
3.  **Create Settlement Account**: A unique `LegacySettlementAccount` is created.
4.  **Escrow Transfer**: All assets from the deceased's accounts are transferred to the `LegacySettlementAccount`. This is a single, atomic bulk transfer.
5.  **Heir & Creditor Identification**: The system identifies all legal heirs and creditors.
6.  **Settlement Execution**: The `SettlementSystem` executes the distribution logic:
    - Calculate and pay inheritance tax to the government.
    - Transfer remaining assets to the heir(s) based on inheritance rules.
7.  **Zero-Balance Verification**: The `SettlementSystem` verifies that the `LegacySettlementAccount` balance is exactly zero. Any discrepancy will raise a critical exception.
8.  **Closure**: The `LegacySettlementAccount` is closed and archived.

### 3.3. Key Components
- **`LegacySettlementAccount` (Data Class)**:
    - `deceased_agent_id`: ID of the deceased.
    - `escrow_assets`: A dictionary or container for various asset types.
    - `status`: (e.g., `OPEN`, `PROCESSING`, `CLOSED`, `ERROR`).
- **`SettlementSystem` (Service/Module)**:
    - `create_settlement(agent_id)`: Initiates the process.
    - `execute_settlement(account_id)`: Processes the distribution.
    - `verify_and_close(account_id)`: Finalizes the transaction.

## 4. Zero-Sum Integrity
- The entire settlement process within the `SettlementSystem` will be wrapped in a single database transaction.
- Auditable logs will be generated for each step of the settlement.
- A post-transaction check will verify that the total value of assets distributed equals the initial escrowed value.

## 5. Action Items
- [ ] Implement the `LegacySettlementAccount` data structure.
- [ ] Implement the `SettlementSystem` module with its core methods.
- [ ] Integrate the `SettlementSystem` with the `PopulationManager`'s death event handler.
- [ ] Replace the old direct transfer logic with a call to `SettlementSystem.create_settlement()`.
- [ ] Add unit tests to verify atomicity and zero-sum guarantees.
