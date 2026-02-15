# Insight Report: Spec 17.3 Config & Protocol Purity

## Architectural Insights

### 1. The "Ghost Constant" Trap
The codebase currently relies heavily on `from config import X`. This creates a rigid dependency graph where values are "baked in" at process start.
-   **Impact**: Runtime adjustments (e.g., God Mode commands, AI Curriculum changes) are silently ignored by modules that have already imported the constant.
-   **Correction**: Moving to `import config` acts as a Service Locator for configuration, ensuring `config.X` always hits the `GlobalRegistry`.
-   **Implementation**: Refactored `config/__init__.py` to be a pure proxy around `GlobalRegistry`. Moved constants to `config/defaults.py` to prevent import-time binding.

### 2. Protocol Interface Segregation
`ISettlementSystem` was identified as a "God Interface", mixing standard agent capabilities (Transfer) with Admin capabilities (Minting).
-   **Decision**: Split into `ISettlementSystem` (Standard) and `IMonetaryAuthority` (Admin).
-   **Benefit**: Agents can be tested with strict mocks of `ISettlementSystem` without needing to stub out administrative methods they should never call.
-   **Implementation**: `SettlementSystem` now implements `IMonetaryAuthority` (which inherits `ISettlementSystem`). `Government` agent uses `ISettlementSystem` but specialized services (like `FiscalBondService`) might need elevated privileges (handled via dependency injection).

## Technical Debt Ledger

| ID | Type | Description | Remediation Plan |
| :--- | :--- | :--- | :--- |
| **TD-CONF-01** | Architecture | `config/__init__.py` contains hardcoded defaults mixed with logic. | **Resolved**: Extracted defaults to `config/defaults.py`. |
| **TD-TEST-01** | Testing | Tests use `MagicMock()` without specs, allowing drift. | **Resolved**: Enforced `spec=Protocol` in `conftest.py` fixtures and added `assert_implements_protocol` utility. |
| **TD-IMP-01** | Architecture | `simulation/systems/demographic_manager.py` had a broken import pointing to `modules.simulation.api`. | **Resolved**: Fixed import to point to `modules.household.api`. |

## Pre-Implementation Test Evidence

*Tests passing after implementation:*

```
tests/integration/test_config_hot_swap.py::test_config_hot_swap PASSED   [ 20%]
tests/integration/test_config_hot_swap.py::test_config_engine_type_access PASSED [ 40%]
tests/unit/test_strict_mocking.py::test_strict_mock_isettlement_system PASSED [ 60%]
tests/unit/test_strict_mocking.py::test_strict_mock_imonetary_authority PASSED [ 80%]
tests/unit/test_strict_mocking.py::test_protocol_enforcer_utility PASSED [100%]

============================== 5 passed in 0.41s ===============================
```

*Regression Testing:*
```
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_qe PASSED [ 19%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_fail PASSED [ 22%]
...
tests/unit/systems/test_settlement_system.py::test_transfer_success PASSED [ 35%]
...
tests/unit/systems/test_settlement_system.py::test_atomic_settlement_success PASSED [ 64%]
...
============================== 31 passed in 0.50s ==============================
```
