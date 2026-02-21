# Fix Public Manager Funding & Escheatment

## Architectural Insights

### 1. Soft Budget Constraint for System Agents
To solve the "Liquidity Trap" where the Public Manager (PM) could not acquire assets from bankrupt firms due to lack of funds, we introduced the `ISystemFinancialAgent` protocol. Agents implementing this protocol (and returning `True` from `is_system_agent()`) are exempt from strict solvency checks in the `SettlementSystem` and `TransactionEngine`.

- **Implementation**:
    - `ISystemFinancialAgent` added to `modules/system/api.py`.
    - `PublicManager` implements this protocol.
    - `SettlementSystem._prepare_seamless_funds` and `FinancialAgentAdapter.allows_overdraft` updated to check for this marker.

### 2. Asset Buyout Mechanism
The escheatment process was split into two phases to allow liquidity injection before final cleanup:
- **Phase A (Asset Buyout)**: PM purchases assets from the bankrupt agent using `execute_asset_buyout`. This injects cash into the bankrupt agent (potentially driving PM balance negative).
- **Phase C (Residual Escheatment)**: Remaining cash and assets are transferred to the Government.

- **DTOs**: `AssetBuyoutRequestDTO` and `AssetBuyoutResultDTO` standardized the data flow.

### 3. Deficit Tracking
The `PublicManager` now tracks `cumulative_deficit`, which represents the total amount of "new money" created via overdrafts to fund bailouts/buyouts. This metric is exposed via `get_deficit()` and included in the `PublicManagerReportDTO`.

## Regression Analysis

### 1. Public Manager Compliance
`tests/unit/modules/system/execution/test_public_manager_compliance.py` was updated.
- **Before**: Expected `InsufficientFundsError` on overdraft.
- **After**: Verifies that overdraft is allowed and deficit is tracked.
- **Reason**: The core requirement was to enable overdraft.

### 2. Settlement System Integrity
`tests/unit/finance/test_settlement_system_overdraft.py` was created to ensure:
- Normal agents **cannot** overdraft (Zero-Sum Integrity preserved for them).
- System agents **can** overdraft (Soft Budget Constraint).

### 3. Escheatment Logic
`simulation/systems/handlers/escheatment_handler.py` was refactored but maintains backward compatibility for legacy escheatment if no subtype is specified (defaults to residual cash logic).

## Test Evidence

```
tests/unit/modules/system/execution/test_public_manager_compliance.py::TestPublicManagerCompliance::test_implements_financial_agent PASSED [  6%]
tests/unit/modules/system/execution/test_public_manager_compliance.py::TestPublicManagerCompliance::test_implements_system_financial_agent PASSED [ 13%]
tests/unit/modules/system/execution/test_public_manager_compliance.py::TestPublicManagerCompliance::test_implements_asset_recovery_system PASSED [ 20%]
tests/unit/modules/system/execution/test_public_manager_compliance.py::TestPublicManagerCompliance::test_bankruptcy_processing_id_handling
-------------------------------- live log call ---------------------------------
WARNING  PublicManager:public_manager.py:93 Processing bankruptcy for Agent 99 at tick 1. Recovering inventory.
INFO     PublicManager:public_manager.py:98 Recovered 10.0 of gold.
PASSED                                                                   [ 26%]
tests/unit/modules/system/execution/test_public_manager_compliance.py::TestPublicManagerCompliance::test_liquidation_order_generation_id
-------------------------------- live log call ---------------------------------
INFO     PublicManager:public_manager.py:168 Generated liquidation order for 1.0 of gold at 95.0.
PASSED                                                                   [ 33%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_process_bankruptcy_event
-------------------------------- live log call ---------------------------------
WARNING  PublicManager:public_manager.py:93 Processing bankruptcy for Agent 1 at tick 10. Recovering inventory.
INFO     PublicManager:public_manager.py:98 Recovered 10.0 of apple.
INFO     PublicManager:public_manager.py:98 Recovered 5.0 of banana.
PASSED                                                                   [ 40%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_generate_liquidation_orders
-------------------------------- live log call ---------------------------------
INFO     PublicManager:public_manager.py:168 Generated liquidation order for 50.0 of apple at 9.0.
PASSED                                                                   [ 46%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_confirm_sale PASSED [ 53%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_deposit_revenue PASSED [ 60%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_generate_liquidation_orders_no_signal PASSED [ 66%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_generate_liquidation_orders_resets_metrics PASSED [ 73%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_execute_asset_buyout
-------------------------------- live log call ---------------------------------
INFO     PublicManager:public_manager.py:120 Executed Asset Buyout from Agent 1. Paid: 500, Items: 1
PASSED                                                                   [ 80%]
tests/unit/finance/test_settlement_system_overdraft.py::TestSettlementSystemOverdraft::test_normal_agent_cannot_overdraft
-------------------------------- live log call ---------------------------------
ERROR    simulation.systems.settlement_system:settlement_system.py:358 SETTLEMENT_FAIL | Insufficient funds. Cash: 100, Req: 200.
PASSED                                                                   [ 86%]
tests/unit/finance/test_settlement_system_overdraft.py::TestSettlementSystemOverdraft::test_system_agent_can_overdraft
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.settlement_system:engine.py:126 Transaction Record: ID=fa6431ba-e4f4-456e-8406-7fae3fd09206, Status=COMPLETED, Message=Transaction successful.
PASSED                                                                   [ 93%]
tests/integration/test_public_manager_integration.py::TestPublicManagerIntegration::test_full_liquidation_cycle
-------------------------------- live log call ---------------------------------
WARNING  PublicManager:public_manager.py:93 Processing bankruptcy for Agent 99 at tick 1. Recovering inventory.
INFO     PublicManager:public_manager.py:98 Recovered 10.0 of gold.
INFO     PublicManager:public_manager.py:168 Generated liquidation order for 10.0 of gold at 100.0.
PASSED                                                                   [100%]
======================== 15 passed, 2 warnings in 0.33s ========================
```
