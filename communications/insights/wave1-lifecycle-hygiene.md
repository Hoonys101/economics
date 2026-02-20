# Insight Report: Wave 1.2 System Lifecycle & Dependency Hygiene

**Mission Key**: `wave1-lifecycle-hygiene`
**Date**: 2026-02-20
**Author**: Jules (Architect)

## 1. Architectural Insights

### Dependency Hygiene Resolution
We successfully resolved several critical technical debts related to system coupling and initialization order.

-   **SettlementSystem Initialization (`TD-ARCH-DI-SETTLE`)**: The `SettlementSystem` was previously initialized without an `AgentRegistry`, relying on a post-initialization injection via attribute assignment. This created a fragile window where the system existed but was non-functional (lacking an engine). We refactored `SimulationInitializer` to instantiate `AgentRegistry` first and inject it directly into the `SettlementSystem` constructor. This enforces "Constructor Dependency Injection", making the dependency explicit and the object valid upon creation.

-   **Protocol Purity in Transactions (`TD-PROTO-MONETARY`)**: The `MonetaryTransactionHandler` relied on concrete `Firm` class checks (`isinstance(seller, Firm)`). We introduced a new `IIssuer` protocol in `modules/common/interfaces.py` (defining `id`, `treasury_shares`, `total_shares`). The handler now checks against this protocol, decoupling the transaction logic from the specific agent implementation.

### DTO Purity Enforcement
-   **Analytics Encapsulation (`TD-ANALYTICS-DTO-BYPASS`)**: `AnalyticsSystem` was bypassing the DTO boundary by calling `agent.get_quantity()` directly on agent instances. We refactored this to strictly use `HouseholdSnapshotDTO` (specifically `econ_state.inventory`) and `FirmStateDTO` (`production.inventory`). This ensures that the analytics subsystem relies only on immutable state snapshots, preserving the "Stateless Engine" architecture.

## 2. Regression Analysis & Fixes

### 1. `SettlementSystem` Engine Initialization
-   **Regression**: Tests accessing `SettlementSystem.settle_atomic` failed with `AttributeError: 'SettlementSystem' object has no attribute '_transaction_engine'`.
-   **Cause**: The `_transaction_engine` attribute was previously initialized in `set_panic_recorder`, which was optional or called late. With the new constructor injection, usage patterns in tests triggered execution paths expecting the engine earlier.
-   **Fix**: Moved the initialization of `self._transaction_engine = None` and auxiliary dictionaries (`_bank_depositors`, `_agent_banks`) to `__init__`.

### 2. Protocol Adherence in Tests
-   **Regression**: `TestWO157DynamicPricing::test_transaction_processor_calls_record_sale` failed.
-   **Cause**: The test used a `Mock(spec=Firm)` for the seller. The strict runtime check `isinstance(seller, ISalesTracker)` failed because the mock object did not explicitly define the required attribute `sales_volume_this_tick`, which `ISalesTracker` protocol demands.
-   **Fix**: Updated the test setup to explicitly set `seller.sales_volume_this_tick = 0.0` on the mock object, ensuring it satisfies the `@runtime_checkable` protocol.

### 3. DTO Structure in Persistence Tests
-   **Regression**: `test_analytics_system_purity` failed.
-   **Cause**: The test mocked `Household` but did not mock the return structure of `create_snapshot_dto()`. The refactored `AnalyticsSystem` now traverses this DTO (`snapshot.econ_state.inventory`), causing failures on the mock.
-   **Fix**: Updated the test to mock the full DTO hierarchy (`mock_snapshot.econ_state.inventory`), aligning the test double with the new architectural contract.

## 3. Test Evidence

The following output demonstrates that all affected modules pass 100%.

```text
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
plugins: asyncio-0.25.3, cov-6.0.0, anyio-4.8.0, mock-3.14.0
collected 24 items

tests/unit/systems/test_settlement_system.py::test_transfer_success PASSED [  4%]
tests/unit/systems/test_settlement_system.py::test_transfer_insufficient_funds PASSED [  8%]
tests/unit/systems/test_settlement_system.py::test_create_and_transfer_minting PASSED [ 12%]
tests/unit/systems/test_settlement_system.py::test_create_and_transfer_government_grant PASSED [ 16%]
tests/unit/systems/test_settlement_system.py::test_transfer_and_destroy_burning PASSED [ 20%]
tests/unit/systems/test_settlement_system.py::test_transfer_and_destroy_tax PASSED [ 25%]
tests/unit/systems/test_settlement_system.py::test_record_liquidation PASSED [ 29%]
tests/unit/systems/test_settlement_system.py::test_record_liquidation_escheatment PASSED [ 33%]
tests/unit/systems/test_settlement_system.py::test_transfer_rollback PASSED [ 37%]
tests/unit/systems/test_settlement_system.py::test_transfer_insufficient_cash_despite_bank_balance PASSED [ 41%]
tests/unit/systems/test_settlement_system.py::test_transfer_insufficient_total_funds PASSED [ 45%]
tests/unit/systems/test_settlement_system.py::test_execute_multiparty_settlement_success PASSED [ 50%]
tests/unit/systems/test_settlement_system.py::test_execute_multiparty_settlement_rollback PASSED [ 54%]
tests/unit/systems/test_settlement_system.py::test_settle_atomic_success PASSED [ 58%]
tests/unit/systems/test_settlement_system.py::test_settle_atomic_rollback PASSED [ 62%]
tests/unit/systems/test_settlement_system.py::test_settle_atomic_credit_fail_rollback PASSED [ 66%]
tests/integration/test_persistence_purity.py::test_analytics_system_purity PASSED [ 70%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_record_sale_updates_tick PASSED [ 75%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_dynamic_pricing_reduction PASSED [ 79%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_dynamic_pricing_floor PASSED [ 83%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_dynamic_pricing_not_stale PASSED [ 87%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_transaction_processor_calls_record_sale PASSED [ 91%]
tests/unit/test_tax_incidence.py::TestTaxIncidence::test_firm_payer_scenario PASSED [ 95%]
tests/unit/test_tax_incidence.py::TestTaxIncidence::test_household_payer_scenario PASSED [100%]

============================== 24 passed in 0.53s ==============================
```
