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
