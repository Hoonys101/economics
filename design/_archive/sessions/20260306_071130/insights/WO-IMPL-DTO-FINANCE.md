---
mission_key: "WO-IMPL-DTO-FINANCE"
date: "2026-03-05"
target_manual: "TECH_DEBT_LEDGER.md"
actionable: true
---

# Insight Report: Finance & WorldState Decoupling

## 1. Architectural Insights
- **Identified Debt (TD-ARCH-FINANCE-COUPLING)**: `FinanceSystem` and `CentralBankSystem` were structurally entangled with `WorldState`. Core macro-financial operations, such as `evaluate_solvency` and bond issuance, relied on accessing mutable agent state properties directly (e.g., `firm.balance_pennies`) or manually mutating global simulation structures instead of routing via strict Protocols.
- **Decision**: Promoted `ISettlementSystem` to the strict Single Source of Truth (SSoT) for all transactional balances. All liquidity checks in the `FinanceSystem` MUST now use `ISettlementSystem.get_balance()`. Promoted `IMonetaryLedger` as the SSoT for M2 Supply and System Debt. `WorldState`'s macro-metric getters now strictly proxy to `IMonetaryLedger`.
- **DTO Purity Implementation**: Introduced `FirmFinancialSnapshotDTO` to replace passing mutable `IFinancialFirm` instances into the solvency engines, eliminating God Class leakage into the finance domain.

## 2. Regression Analysis
- **Broken Tests**: Existing system tests in `tests/finance/test_solvency_logic.py` and `tests/unit/modules/finance/test_system.py` failed with `AttributeError` because they mocked `firm.balance_pennies` as a direct property during bailout checks and passed raw Firm instances. `WorldState` initialization tests needed verification that `calculate_total_money` proxied properly to the ledger.
- **Fix**: Refactored the test fixtures. Replaced mock `IFinancialFirm` objects with `FirmFinancialSnapshotDTO` generation in affected tests. Injected `MagicMock(spec=ISettlementSystem)` into `FinanceSystem` setup and configured `mock_settlement_system.get_balance.return_value` to simulate reserves, aligning the suite with the stateless engine pattern.

## 3. Test Evidence
```text
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pyproject.toml
plugins: mock-3.15.1, asyncio-1.3.0, anyio-4.12.1
collected 57 items

tests/finance/test_account_registry.py .................
tests/finance/test_account_registry_threads.py .
tests/finance/test_adapter_caching.py .
tests/finance/test_circular_imports_fix.py .
tests/finance/test_monetary_expansion_handler.py ..
tests/finance/test_protocol_integrity.py .....
tests/finance/test_settlement_fx_swap.py ...
tests/finance/test_settlement_integrity.py ....
tests/finance/test_solvency_logic.py ....
tests/unit/modules/finance/test_corporate_finance.py .....
tests/unit/modules/finance/test_double_entry.py ....
tests/unit/modules/finance/test_monetary_engine.py .
tests/unit/modules/finance/test_qe.py ...
tests/unit/modules/finance/test_settlement_purity.py .
tests/unit/modules/finance/test_sovereign_debt.py .
tests/unit/modules/finance/test_system.py ....

============================= 57 passed in 25.07s ==============================
```
