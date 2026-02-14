# Insight Report: Financial Integrity Hardening

**Date**: 2026-02-14
**Mission**: `lane-2-settlement-integrity`
**Author**: Jules (AI)

## 1. Architectural Insights

### A. The "Float Leak" Discovered
By hardening `SettlementSystem` to strictly reject non-integer amounts, I uncovered a real "leak" in `InventoryLiquidationHandler`.
- **The Bug**: `InventoryLiquidationHandler` calculated liquidation value as `price * qty * (1.0 - haircut)` which resulted in a `float`.
- **The Risk**: This float was passed to `SettlementSystem.transfer`. Before my changes, it was likely silently cast or accepted (depending on the implementation details at the time, or if using Mocks). With strict checking, it raised `TypeError`.
- **The Fix**: Explicitly converted the total value to integer pennies (`int(total_value * 100)`) before transfer. This ensures zero-sum integrity is maintained at the penny level.

### B. Protocol Unification
The `ISettlementSystem` protocol was fragmented across `modules/finance/api.py` and `simulation/finance/api.py`.
- I unified them by updating `modules/finance/api.py` to match the `SettlementSystem` implementation (strict `amount: int`, `debit_agent`/`credit_agent` naming).
- I added `mint_and_distribute` to `simulation/finance/api.py` (ABC), ensuring `CommandService` relies on a formal contract rather than implicit method availability.

### C. Test Suite Fragility & Strictness
Enforcing strict types revealed fragility in tests:
- `test_server_bridge.py`: Was passing loose strings to `TelemetryExchange`. Updated to use strict `TelemetrySnapshotDTO`.
- `test_housing_connector.py`: Mocked system failed `isinstance(mock, IHousingSystem)` check. Updated to use `create_autospec`.
- `test_liquidation_handlers.py`: Tests were asserting float values (`40.0`) instead of pennies (`4000`).

## 2. Test Evidence

The full test suite passed (750 tests).

```
=========================== short test summary info ============================
SKIPPED [1] tests/unit/decisions/test_household_integration_new.py:12: TODO: Fix integration test setup. BudgetEngine/ConsumptionEngine interaction results in empty orders.
================= 750 passed, 1 skipped, 10 warnings in 13.34s =================
```

### Verification of Settlement Integrity
I created `tests/finance/test_settlement_integrity.py` to specifically verify the strict checks:

```python
    def test_transfer_float_raises_error(self, settlement_system):
        # ...
        with pytest.raises(TypeError, match="Settlement integrity violation"):
            settlement_system.transfer(..., amount=100.0, ...)
```

This test now passes (meaning the `TypeError` IS raised), confirming the guardrails are active.
