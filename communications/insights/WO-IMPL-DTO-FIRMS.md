---
mission_key: "WO-IMPL-DTO-FIRMS"
date: "2026-03-05"
target_manual: "TECH_DEBT_LEDGER.md"
actionable: true
---

### [Architectural Insights]
- **Market State Decoupling**: Identified `MAManager` and `FirmSystem` as being tightly coupled to `WorldState.markets`. By transitioning `simulation.markets` queries to `MarketStateDTO`, we eliminate `hasattr()` evasion (`TD-ARCH-PROTOCOL-EVASION`) and move toward a strictly typed, stateless engine pattern.
- **FirmFactory Signature Update**: `FirmFactory` previously received live `loan_market` objects via `kwargs`, creating a dependency loop and allowing unintended state mutation. Switching this injection to `loan_market_state: Optional[MarketStateDTO]` directly in the `Firm` constructor resolves state mutability risks during firm generation and enforces DTO decoupling at the boundary layer.

### [Regression Analysis]
- Existing tests mocking `simulation.markets` encountered failures due to `process_market_exits_and_entries` and `spawn_firm` requiring `markets_state: Dict[str, MarketStateDTO]`. We updated the test mocks and implemented fallback extraction mechanisms within the methods.
- The `Firm` initialization step failed when the `loan_market` argument was completely removed because some tests and systems still relied on passing it as a `kwargs` component. We updated the `__init__` constructor signature to safely handle both `loan_market_state` natively and fallback gracefully for legacy `kwargs`, migrating strictly towards DTOs.
- `AnalyticsSystem` initialization had a missing `Optional` import in type hints that surfaced during test execution, which was rectified immediately to maintain protocol purity.

### [Test Evidence]
```
tests/unit/systems/test_ma_manager.py::TestMAManager::test_execute_bankruptcy_records_loss_in_ledger
PASSED                                                                   [ 50%]
tests/simulation/test_firm_factory.py::TestFirmFactoryAtomicRegistration::test_firm_atomic_registration
PASSED                                                                   [ 50%]
tests/simulation/test_firm_factory.py::TestBootstrapperProtocolPurity::test_bootstrapper_protocol_purity
PASSED                                                                   [100%]
tests/unit/systems/test_firm_management_leak.py::TestFirmManagementLeak::test_spawn_firm_leak_detection
PASSED                                                                   [100%]
tests/unit/systems/test_firm_management_refactor.py::TestFirmManagementRefactor::test_spawn_firm_missing_settlement_system
PASSED                                                                   [ 50%]
tests/unit/systems/test_firm_management_refactor.py::TestFirmManagementRefactor::test_spawn_firm_transfer_failure
PASSED                                                                   [100%]
tests/unit/markets/test_loan_market.py::TestLoanMarket::test_initialization
PASSED                                                                   [ 16%]
tests/unit/markets/test_loan_market.py::TestLoanMarket::test_place_loan_request_grants_loan
PASSED                                                                   [ 33%]
tests/unit/markets/test_loan_market.py::TestLoanMarket::test_place_loan_request_with_profile
PASSED                                                                   [ 50%]
tests/unit/markets/test_loan_market.py::TestLoanMarket::test_place_loan_request_denies_loan
PASSED                                                                   [ 66%]
tests/unit/markets/test_loan_market.py::TestLoanMarket::test_place_repayment_processes_repayment
PASSED                                                                   [ 83%]
tests/unit/markets/test_loan_market.py::TestLoanMarket::test_place_order_unknown_type_logs_warning
PASSED                                                                   [100%]

============================== 12 passed in 6.94s ==============================
```
