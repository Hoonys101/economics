# Mission Insights: Bundle 6 Engine Hardening

## Technical Debt & Issues Uncovered

### 1. Multi-Currency Type Fragility
The migration to `MultiCurrencyWallet` (using `Dict[CurrencyCode, float]`) instead of `float` for assets/balance has caused widespread `TypeError`s throughout the system.
- **Root Cause**: Many subsystems (MAManager, CommerceSystem, HRStrategy) still expected `float`.
- **Fix Applied**: Updated critical paths to use `balance.get(DEFAULT_CURRENCY, 0.0)`.
- **Recommendation**: Introduce a `Wallet` adapter or property on agents that automatically returns the default currency value when accessed as a float (via `__float__` magic method if possible, or a dedicated property like `cash_equivalent`). Or strictly enforce DTOs that handle this.

### 2. SagaHandler Dependency Injection
`HousingTransactionSagaHandler` in `modules/finance/saga_handler.py` expects `simulation` to have `housing_service`, but it receives `SimulationState` (DTO) which does not have services.
- **Workaround**: Changed access to `getattr(simulation, 'housing_service', None)`.
- **Impact**: Housing sagas may fail silently or behave incorrectly if service is missing.
- **Recommendation**: Refactor `SettlementSystem.process_sagas` to pass the `WorldState` or `Simulation` instance, not just `SimulationState`.

### 3. Agent Registry Integrity (Government in Employees)
`LifecycleManager` crashed because `Government` agent was found in `firm.hr.employees`.
- **Observation**: `AttributeError: 'Government' object has no attribute 'is_active'`.
- **Fix Applied**: Added `hasattr(emp, 'is_active')` check.
- **Risk**: This suggests a logic error in `Hiring` or `M&A` (State Capture) where the Government entity is being added to employee lists.

### 4. Wallet Initialization (NoneType)
Crash in `SettlementSystem` because `agent.wallet` was `None`.
- **Observation**: Happened during `EmergencyHandler` execution (Tick 8).
- **Risk**: Agents (likely Households) are existing without initialized Wallets. This might be due to `clone()` or specific initialization paths in `scenario_stress_100.py`.

### 5. Snapshot Verification
`PersistenceBridge` was not being invoked in `scenario_stress_100.py`.
- **Fix**: Manually instantiated `DashboardService` and called `get_snapshot()` in the scenario loop.
- **Insight**: Scenarios run in isolation and may bypass standard orchestration services (like `server.py`). Standardizing the runner (e.g. using `SimulationEngine` that always includes `DashboardService`) is recommended.

## Accomplishments
- Fixed Tick 2 Crash (`CommerceSystem` & `MAManager`).
- Fixed Tick 36 Crash (`LifecycleManager` & `SagaHandler`).
- Fixed Tick 3 Crash (`HRStrategy`).
- Verified Snapshot generation.
- Refactored DTOs (`FirmStateDTO`).
