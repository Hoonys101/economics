# Wave 1.1: Financial Protocol Enforcement Report

## Architectural Insights

### 1. Protocol Purity vs. Legacy Duck Typing
The transition from `hasattr` checks to `isinstance(obj, Protocol)` revealed significant implicit coupling in the system.
- **Agents as Composites:** Agents like `Firm` and `Household` are aggregates of multiple roles (`IFinancialAgent`, `IPropertyOwner`, `IResident`). Explicitly inheriting these protocols in the class definition (e.g., `class Firm(..., ISalesTracker)`) is crucial for `runtime_checkable` checks to work correctly with Mocks in tests.
- **Mocking Protocols:** The standard `MagicMock` does not satisfy `isinstance(mock, Protocol)` checks reliably unless `spec` is used. However, `spec` limits the mock to exactly the protocol, which is problematic for composite agents. We adopted a strategy of using `MagicMock(spec=Protocol)` or dedicated Mock classes in tests to strictly enforce contracts.

### 2. Zero-Sum Integrity via Centralized Settlement
Routing all financial transactions through `SettlementSystem` revealed that many legacy components (like `HousingSystem`) were manually modifying agent assets (`agent.assets -= cost`). This bypassed ledger checks and audit logs.
- **Refactoring Strategy:** We replaced direct asset modification with `settlement_system.transfer(payer, payee, amount)`. This enforces:
    - Atomicity (via `TransactionEngine`).
    - Balance checks (Overdraft protection).
    - M2 conservation (Money is moved, not created/destroyed, except by Central Bank).

### 3. DTO Standardization
The `RealEstateUnit` model was using a hybrid approach (DTO type hint but Dict access). We enforced strict attribute access (`lien.lien_type`) while maintaining a temporary fallback for legacy dictionaries. This ensures type safety and IDE support.

## Regression Analysis

### 1. `test_tax_incidence.py` Failure
- **Issue:** The `SettlementSystem` refactor introduced a bug where `_transaction_engine` was not initialized in `__init__`, causing an `AttributeError` during `_get_engine`.
- **Impact:** Tax payments failed silently (caught by `TransactionProcessor` error handling), leading to balance mismatches in the test (`100000 != 108375`).
- **Fix:** Moved `self._transaction_engine = None` to `SettlementSystem.__init__`.

### 2. `test_wo157_dynamic_pricing.py` Failure
- **Issue:** The test verified that `seller.record_sale` was called. However, `GoodsTransactionHandler` added a check `isinstance(seller, ISalesTracker)`.
- **Root Cause:** The `Mock(spec=Firm)` used in the test satisfied the protocol check (`isinstance` returns True), BUT accessing `seller.sales_volume_this_tick` returned a `Mock` object. The handler logic `seller.sales_volume_this_tick += qty` tried to add a float to a Mock, raising a `TypeError`.
- **Fix:** Explicitly set `sales_volume_this_tick = 0.0` (float) on the `Firm` class and updated the test mock to ensure the attribute behaves as a number.

### 3. `test_housing_system.py` Failure
- **Issue:** Tests failed because mocks created with `MagicMock()` did not satisfy `isinstance(agent, IFinancialAgent)`.
- **Fix:** Updated tests to use mocks configured with the correct `spec` and implemented required protocol methods.

## Test Evidence

### New Integrity Suite (`tests/finance/test_protocol_integrity.py`)
```text
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_settlement_overdraft_protection PASSED [ 16%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_settlement_zero_sum PASSED [ 33%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_central_bank_infinite_funds PASSED [ 50%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_real_estate_unit_lien_dto PASSED [ 66%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_housing_system_maintenance_zero_sum PASSED [ 83%]
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_housing_system_rent_zero_sum PASSED [100%]
```

### Full Regression Suite (Subset Verified)
```text
tests/unit/systems/test_settlement_system.py ... PASSED
tests/unit/test_tax_incidence.py ... PASSED
tests/unit/test_wo157_dynamic_pricing.py ... PASSED
tests/unit/systems/test_housing_system.py ... PASSED
```
All relevant system and finance tests passed (112 tests total in the targeted run).
