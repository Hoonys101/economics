# Insight: Estate Registry Pattern (Graveyard)
# MISSION_ID: WO-IMPL-ESTATE-REGISTRY
# DATE: 2026-02-25
# AUTHOR: Jules

## 1. Architectural Insights

### The "Limbo" Problem in Double-Entry Accounting
In a strict zero-sum simulation, an entity cannot simply "cease to exist" if it holds assets or liabilities. Previously, `DeathSystem` deleted agents from the registry immediately upon liquidation. However, asynchronous processes (like `EscheatmentHandler` transferring remaining assets to the government) would fail because the agent no longer existed in the registry, leading to `KeyError` or requiring fragile "Resurrection Hacks" (temporarily re-injecting the agent).

### The Solution: Estate Registry
We introduced `simulation/registries/estate_registry.py` and the `IEstateRegistry` protocol. This creates a formal "Graveyard" state.
- **Before:** Active -> Deleted (Instant)
- **After:** Active -> Estate (Graveyard) -> Deleted (Eventually/Never)

The `EstateRegistry` holds references to agents that have been removed from the active simulation but still require financial settlement.

### Transparent Fallback in AgentRegistry
Instead of modifying every call site (e.g., `SettlementSystem`), we modified `AgentRegistry.get_agent(id)` to transparently check the `EstateRegistry` if the agent is not found in the active state. This effectively implements the **Null Object Pattern** or **Fallback Pattern** for deceased agents, allowing financial systems to interact with them as if they were still active for settlement purposes.

## 2. Regression Analysis

### Pennies vs Dollars in M2 Integrity
During verification, `tests/integration/test_m2_integrity.py` failed because it asserted `delta == 1000.0` (Dollars) when the system returned `100000` (Pennies).
- **Cause:** The codebase has been migrating to a strict "Penny Standard" (Integer Math), but this specific test file was legacy code using floats.
- **Fix:** Updated the test assertions to expect integer pennies (`100000`), aligning the test with the current system architecture.

### M2 Calculation Scope
`WorldState.calculate_total_money` was updated to iterate over BOTH `self.agents.values()` (active) and `self.estate_registry.get_all_estate_agents()` (dead). This ensures that money held by dead agents (before escheatment) is not "leaked" from the M2 Money Supply audit.

## 3. Test Evidence

### `pytest tests/integration/test_liquidation_waterfall.py tests/integration/test_m2_integrity.py`

```text
tests/integration/test_liquidation_waterfall.py::TestLiquidationWaterfallIntegration::test_asset_rich_cash_poor_liquidation
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.liquidation_handlers:liquidation_handlers.py:85 LIQUIDATION_ASSET_SALE | Agent 1 sold inventory to PublicManager for 80000.
INFO     simulation.systems.liquidation_manager:liquidation_manager.py:81 LIQUIDATION_START | Agent 1 starting liquidation. Assets: 80000.0, Total Claims: 500
INFO     simulation.systems.liquidation_manager:liquidation_manager.py:126 LIQUIDATION_WATERFALL | Tier 1 fully paid. Remaining cash: 79500.0
PASSED                                                                   [ 16%]
tests/integration/test_liquidation_waterfall.py::TestLiquidationWaterfallIntegration::test_severance_priority_over_shareholders
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.liquidation_manager:liquidation_manager.py:81 LIQUIDATION_START | Agent 1 starting liquidation. Assets: 5000.0, Total Claims: 5614
INFO     simulation.systems.liquidation_manager:liquidation_manager.py:134 LIQUIDATION_WATERFALL | Tier 1 partially paid (Factor: 0.89). Cash exhausted.
PASSED                                                                   [ 33%]
tests/integration/test_liquidation_waterfall.py::TestLiquidationWaterfallIntegration::test_waterfall_tiers
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.liquidation_manager:liquidation_manager.py:81 LIQUIDATION_START | Agent 1 starting liquidation. Assets: 10000.0, Total Claims: 7003
INFO     simulation.systems.liquidation_manager:liquidation_manager.py:126 LIQUIDATION_WATERFALL | Tier 1 fully paid. Remaining cash: 7997.0
INFO     simulation.systems.liquidation_manager:liquidation_manager.py:126 LIQUIDATION_WATERFALL | Tier 2 fully paid. Remaining cash: 2997.0
INFO     simulation.systems.liquidation_manager:liquidation_manager.py:180 LIQUIDATION_WATERFALL | Tier 5 (Equity) distributed 1498.50 USD and foreign assets: {} to shareholders.
PASSED                                                                   [ 50%]
tests/integration/test_m2_integrity.py::TestM2Integrity::test_credit_creation_expansion PASSED [ 66%]
tests/integration/test_m2_integrity.py::TestM2Integrity::test_credit_destruction_contraction PASSED [ 83%]
tests/integration/test_m2_integrity.py::TestM2Integrity::test_internal_transfers_are_neutral PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.pyenv/versions/3.12.12/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.pyenv/versions/3.12.12/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
========================= 6 passed, 1 warning in 0.70s =========================
```
