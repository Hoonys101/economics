# Architectural Insights: Phase 22 [W1] Startup Foundation

## 1. Architectural Insights
- **Initialization Race Conditions**: The `SimulationInitializer` previously linked `AgentRegistry` to `WorldState` before all system agents (specifically `PublicManager` and `CentralBank`) were instantiated. This caused `TD-FIN-INVISIBLE-HAND`, where these agents were missing from the registry snapshot used by `SettlementSystem`. Moving the registry linkage to *after* all system agent creation resolved this.
- **Factory Responsibilities**: The `FirmFactory` was previously a simple object creator. To solve `TD-LIFECYCLE-GHOST-FIRM` (firms existing without bank accounts), we elevated `FirmFactory` to handle the atomic sequence of **Instantiation -> Registration -> Bank Account Opening -> Liquidity Injection**. This ensures no "ghost" firms can exist in a valid state.
- **DTO Hygiene**: `SimulationState` contained a deprecated `governments` list field alongside `primary_government`, causing confusion (`TD-ARCH-GOV-MISMATCH`). We enforced a strict Singleton pattern by removing the list and ensuring `TickOrchestrator` only populates `primary_government`.
- **TickOrchestrator Hardening**: We added defensive `getattr` calls in `TickOrchestrator` when populating `SimulationState`. This makes the system more robust to partial states during testing or initialization.

## 2. Regression Analysis
- **Breaking Change in FirmFactory**: The signature of `FirmFactory.create_firm` was updated to require `settlement_system` and optional `central_bank`. This was necessary to enforce the atomic creation sequence.
    - **Mitigation**: We verified that existing tests (`tests/utils/factories.py`) instantiate `Firm` directly via constructor, bypassing the factory, thus avoiding immediate regressions. The factory is primarily for runtime agent creation (Lifecycle System).
- **Initialization Order**: Changing the order of `PublicManager` instantiation in `initializer.py` required ensuring that no other components depended on `AgentRegistry` being linked *before* `PublicManager` existed. We verified that `Bootstrapper` (which relies on registry) runs *after* our new linkage point.
- **ActionProcessor Fix**: `ActionProcessor` duplicated the `SimulationState` creation logic found in `TickOrchestrator`. We had to apply the same fix (removing `governments` argument) to `ActionProcessor` to resolve `TypeError` failures in `test_tax_incidence.py`.

## 3. Test Evidence
Running `pytest tests/unit/test_firms.py` and `pytest tests/unit/test_tax_incidence.py`:

```
============================= test session starts ==============================
platform linux -- Python 3.12.8, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
plugins: anyio-4.8.0, asyncio-0.25.3, cov-6.0.0, mock-3.14.0
asyncio: mode=Mode.STRICT
collected 2 items

tests/unit/test_tax_incidence.py ..                                    [100%]

============================== 2 passed in 0.60s ===============================
```

Running full unit suite (`pytest tests/unit`):
```
============================= test session starts ==============================
...
tests/unit/test_firms.py ........                                        [ 12%]
...
tests/unit/test_transaction_processor.py ........                        [ 97%]
...
======================== 639 passed, 1 warning in 4.19s ========================
```
All tests passed.
