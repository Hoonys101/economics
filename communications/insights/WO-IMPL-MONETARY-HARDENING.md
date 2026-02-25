# WO-IMPL-MONETARY-HARDENING: Insight Report

## 1. Architectural Insights
- **Defensive Coding in Ledgers**: The `MonetaryLedger` was relying on implicit string conversions and potentially unsafe access to `Transaction` metadata. By enforcing `normalize_id` and strict `principal` extraction, we prevent `FloatIncursionError` and `AttributeError` which are critical in financial systems.
- **SSoT for Constants**: Moving `ID_PUBLIC_MANAGER` and `ID_CENTRAL_BANK` to `modules.system.constants` and importing them ensures a Single Source of Truth. The previous hardcoding of `"4"` for PublicManager was a fragile implementation detail that has now been removed.
- **Protocol Purity**: The refactor respects the `Transaction` protocol/dataclass structure, handling `metadata` (which is Optional) safely using `getattr` and dictionary `get` methods.

## 2. Regression Analysis
- **Existing Tests**: `tests/unit/modules/government/components/test_monetary_ledger_expansion.py` was updated to use `ID_PUBLIC_MANAGER` instead of the hardcoded string `"4"`. The logic for asset liquidation was verified to work correctly with the new ID normalization.
- **New Logic Coverage**: Added `test_bond_repayment_principal_logic` to cover the new defensive principal extraction. It verifies:
    - Partial contraction when `principal` is specified (e.g. paying back principal only, not interest).
    - Full contraction fallback when `principal` is missing or invalid.
    - Safe handling of `None` metadata.
- **System Integrity**: Ran `tests/system/` to ensuring core simulation engine and server components remain functional. `tests/test_stub_generator.py` failed due to an unrelated environment issue (missing `_internal` module), but this is outside the scope of this mission and pre-existing.

## 3. Test Evidence

### Unit Tests (Monetary Ledger)
```
$ python -m pytest tests/unit/modules/government/components/test_monetary_ledger_expansion.py

tests/unit/modules/government/components/test_monetary_ledger_expansion.py::TestMonetaryLedgerExpansion::test_asset_liquidation_expansion PASSED [ 25%]
tests/unit/modules/government/components/test_monetary_ledger_expansion.py::TestMonetaryLedgerExpansion::test_bond_repayment_principal_logic PASSED [ 50%]
tests/unit/modules/government/components/test_monetary_ledger_expansion.py::TestMonetaryLedgerExpansion::test_lender_of_last_resort_expansion PASSED [ 75%]
tests/unit/modules/government/components/test_monetary_ledger_expansion.py::TestMonetaryLedgerExpansion::test_other_types_no_expansion PASSED [100%]

============================== 4 passed in 0.85s ===============================
```

### System & Integration Tests (Partial Suite)
```
$ python -m pytest tests/unit/modules/government/ tests/system/

...
tests/system/test_server_security.py::test_server_binding_check_secure PASSED [ 96%]
tests/system/test_server_binding_check_insecure PASSED [ 98%]
tests/system/test_server_properties_proxied PASSED [100%]

============================== 63 passed in 4.65s ==============================
```
