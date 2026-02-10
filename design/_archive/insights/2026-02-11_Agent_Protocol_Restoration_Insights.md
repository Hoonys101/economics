# Mission Insight: Core Agent Restoration & Protocol Alignment

## Mission Context
Restoration of core agent unit/integration tests following major architectural changes (Orchestrator-Engine, Protocol Hardening, DTO Purity).

## Identified Technical Debt & Protocol Drift

### 1. IFinancialAgent Protocol Drift
- **Issue**: The `IFinancialAgent` protocol has evolved to require `withdraw(amount: float, currency: CurrencyCode = DEFAULT_CURRENCY)` and `deposit(...)`. Many integration tests use `MockAgent` implementations that only accept `amount` or rely on implicit `USD` default without handling `currency` argument correctly when called with keyword arguments by newer system components (e.g., `SettlementSystem`).
- **Impact**: Integration tests fail with `TypeError` when systems attempt multi-currency transactions.
- **Remediation**: Updated `MockAgent` in `test_atomic_settlement.py` to fully implement `IFinancialAgent` including `get_balance`.

### 2. Encapsulation Violation in ViewModels
- **Issue**: `EconomicIndicatorsViewModel` directly accessed private state `agent._econ_state.assets` to calculate wealth distribution. This violated encapsulation and broke when `_econ_state.assets` was refactored to return a dictionary (Wallet balance) instead of a float.
- **Impact**: ViewModel crashes or returns incorrect data types (dict vs float) for histograms.
- **Remediation**: Refactored ViewModel to use the public `agent.assets` property (or `agent.total_wealth` / `agent.get_balance(DEFAULT_CURRENCY)`) which guarantees a float return value, respecting the `IFinancialAgent` interface.

### 3. MagicMock Serialization Issues (DTO Purity)
- **Issue**: Tests mocking `Household` agents often mocked `_social_state` as a bare `MagicMock`. When `Household.get_state_dto()` is called (e.g., by `AnalyticsSystem` or logging), it copies fields like `social_state.conformity`. Since these attributes on the mock returned new `MagicMock` objects, the resulting DTO contained Mocks instead of primitives. Attempts to serialize this DTO (e.g., for JSON logs or persistence) caused `TypeError: Object of type MagicMock is not JSON serializable`.
- **Impact**: Persistence and stress scenario tests failed during logging or state capture.
- **Remediation**: Explicitly configured `MagicMock` instances in test fixtures to return primitive values (float/int) for all state attributes accessed by DTO factories.

### 4. Firm State Attribute Rename
- **Issue**: `Firm` agents moved from direct component access (`firm.hr`, `firm.finance`) to state DTOs (`firm.hr_state`, `firm.finance_state`). Integration tests accessing legacy attributes failed.
- **Impact**: `AttributeError` in `test_liquidation_services.py`.
- **Remediation**: Updated tests to use correct state DTO attributes.

## Architectural Recommendations
1. **Strict Mock Factories**: Future tests should use a centralized `MockFactory` that automatically populates state DTO fields with primitives to avoid serialization issues, rather than ad-hoc `MagicMock` setup in each test file.
2. **ViewModel decoupling**: ViewModels should depend on `Repository` or `Service` layers returning DTOs, never on Agent instances directly, to avoid coupling to internal agent structure (`_econ_state`).
