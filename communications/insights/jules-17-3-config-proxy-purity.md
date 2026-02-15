# Insight Report: Spec 17.3 Config & Protocol Purity

## Architectural Insights

### 1. The "Ghost Constant" Trap
The codebase relied on `from config import X` which bound values at import time. This prevented runtime updates (e.g., God Mode) from taking effect in modules that had already imported the configuration.
-   **Resolution**: Refactored `config/__init__.py` to be a dynamic proxy backed by `GlobalRegistry`. Constants were moved to `config/defaults.py`. All known usages of `from config import X` were migrated to `import config` and `config.X`.

### 2. Protocol Interface Segregation
`ISettlementSystem` was a "God Interface", mixing standard agent capabilities (Transfer) with Admin capabilities (Minting, Auditing).
-   **Resolution**: Split into `ISettlementSystem` (Standard) and `IMonetaryAuthority` (Admin).
-   **Impact**: `FinanceSystem` required methods like `register_account` which were missing from the previous `ISettlementSystem` protocol definition but present in the concrete class. These were formalized in `IMonetaryAuthority` (and `ISettlementSystem` in `modules` was updated to include `register_account` in the authority extension).

## Technical Debt Ledger

| ID | Type | Description | Remediation Plan |
| :--- | :--- | :--- | :--- |
| **TD-CONF-01** | Architecture | `config/__init__.py` contained hardcoded defaults. | Extracted to `config/defaults.py`. |
| **TD-TEST-01** | Testing | Tests used loose mocks for `ISettlementSystem`. | Enforced `spec=ISettlementSystem` or `spec=IMonetaryAuthority`. |
| **TD-API-01** | Architecture | `modules/simulation/api.py` was missing `IHouseholdFactory`. | Added missing definitions to fix `ImportError`. |

## Pre-Implementation Test Evidence

Tests `tests/unit/test_config_strictness.py` were created to verify:
1.  **Config Hot-Swap**: Updating registry immediately updates `config.X`.
2.  **Strict Mocking**: `MagicMock(spec=ISettlementSystem)` rejects `mint_and_distribute`, while `MagicMock(spec=IMonetaryAuthority)` accepts it.

All tests passed.
