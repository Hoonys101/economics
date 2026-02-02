I am unable to directly write files to your system. The necessary tools `write_file` or `run_shell_command` are not available to me. I can, however, provide you with the content for the files you requested, and you can create them yourself.

Here is the content for `design/3_work_artifacts/specs/TD-160_Atomic_Inheritance.md`:
```markdown
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
```

Here is the content for `design/3_work_artifacts/specs/TD-187_Prioritized_Severance_Pay.md`:
```markdown
# Spec: TD-187 Liquidation Waterfall Protocol

## 1. Executive Summary
This specification details the **Liquidation Waterfall Protocol** for insolvent firms, addressing the race condition in severance pay (TD-187). It establishes a strict, legally-compliant payment priority to ensure that employee entitlements (severance and wages) are paid before other corporate liabilities like taxes. This prevents over-withdrawal and ensures fair distribution of remaining assets.

## 2. Problem Statement
During firm liquidation, the current system processes payments to various creditors (employees, government) concurrently. This creates a race condition where total withdrawals can exceed the firm's available cash, leading to state inconsistencies. Furthermore, it does not respect the legal priority of employee severance and wages over other debts.

## 3. Proposed Solution: The Liquidation Waterfall

### 3.1. Core Concept
The Liquidation Waterfall implements a sequential, prioritized claims settlement process. When a firm becomes insolvent, its assets are frozen, and a `LiquidationManager` executes payments in a series of tiers. Funds are only allocated to a lower tier if all higher tiers have been fully satisfied.

### 3.2. Payment Priority Tiers (The Waterfall)

1.  **Tier 1: Super-Priority Claims (Employee Entitlements)**
    - **A. Severance Pay**: Accrued severance pay for all employees over the **last 3 years** of service.
    - **B. Unpaid Wages**: Unpaid wages for all employees for the **last 3 months**.

2.  **Tier 2: Secured Creditors**
    - Payments to creditors with collateral (e.g., bank loans secured by firm assets). *(Note: To be defined in more detail as per `finance.yaml`)*.

3.  **Tier 3: Unsecured Priority Claims (Taxes)**
    - Corporate income tax.
    - Other government levies.

4.  **Tier 4: General Unsecured Creditors**
    - Payments to suppliers, bondholders, and other unsecured creditors.

5.  **Tier 5: Equity Holders**
    - Any remaining funds are distributed to shareholders. (In most insolvencies, this tier is not reached).

### 3.3. Protocol Flow
1.  **Insolvency Trigger**: The `FirmManager` or an economic shock event triggers firm liquidation.
2.  **Asset Freeze & Valuation**: All firm bank accounts are frozen. A valuation of total liquid assets is performed.
3.  **Claim Calculation**: The `LiquidationManager` calculates the total claims for each creditor in every tier.
4.  **Waterfall Execution**:
    - The `LiquidationManager` starts at Tier 1.
    - It allocates available funds to satisfy all claims within that tier.
    - **If funds are insufficient to cover a tier**: Funds are distributed pro-rata among creditors within that tier. The waterfall stops, and lower tiers receive nothing.
    - **If funds are sufficient**: The tier is fully paid, and the process moves to the next lower tier with the remaining funds.
5.  **Final Reporting**: A liquidation report is generated detailing the distribution of assets.

### 3.4. Key Components
- **`LiquidationManager` (Service/Module)**:
    - `initiate_liquidation(firm_id)`: Freezes assets and starts the process.
    - `calculate_claims(firm_id)`: Gathers and categorizes all creditor claims.
    - `execute_waterfall(firm_id, claims, available_assets)`: Executes the tiered payment logic.
- **`Claim` (Data Class)**:
    - `creditor_id`: ID of the employee, government, etc.
    - `amount`: The amount owed.
    - `tier`: The priority tier (1-5).

## 4. Action Items
- [ ] Implement the `LiquidationManager` service.
- [ ] Define the `Claim` data structure.
- [ ] Develop logic to accurately calculate severance (last 3 years) and wages (last 3 months).
- [ ] Integrate the `LiquidationManager` into the firm failure/insolvency workflow.
- [ ] Write unit and integration tests to verify the priority logic and pro-rata distribution under various asset-level scenarios.
```
