# Work Order: Alpha & Purity Remediation ()

## 1. Objective
Remediate the critical asset leak (TD-115) and DTO Purity Gate regression (TD-117) as identified in the `Analysis Report: Track Alpha & DTO Purity Recovery`.

## 2. Tasks

### Task 1: Fix TD-115 (Initialization Order)
**Status:** I (Antigravity) have pre-patched `initializer.py`. Jules must verify this fix or adjust if initialization logic changes.
- **File:** `simulation/initialization/initializer.py`
- **Logic:** Ensure `baseline_money_supply` is recorded immediately after `Bootstrapper.inject_initial_liquidity` and BEFORE `Bootstrapper.force_assign_workers` or any `agent.update_needs` calls.

### Task 2: Fix TD-117 (DTO Purity - Demographic Manager)
- **File:** `simulation/systems/demographic_manager.py`
- **Remediation:**
 - Remove direct calls to `parent._sub_assets()`.
 - Inject `SettlementSystem` into the `DemographicManager` via `__init__` or pass it to `process_births`.
 - Use `settlement_system.transfer(parent, newborn, amount, "BIRTH_GIFT")` to handle asset transfers.
 - Ensure `newborn` is registered as a financial entity before transfer.

### Task 3: Fix TD-117 (DTO Purity - Household Lifecycle)
- **File:** `simulation/core_agents.py`
- **Remediation:**
 - Modify `update_needs` to NOT pass `self` into the `LifecycleContext`.
 - If `BioComponent` needs state data, create a `HouseholdStateDTO` or a dedicated `LifecycleDTO` and pass that instead.
 - Update `BioComponent` to accept the DTO.

### Task 4: Verify positive drift (+320.00)
- **Investigation:** After applying Task 1-3, run a 1-tick simulation and check the `MONEY_SUPPLY_CHECK` log.
- **Remediation:** If the +320.00 drift persists, search for any direct `_add_assets` calls in legacy components (e.g., `RefluxSystem.distribute` or `HousingSystem.apply_homeless_penalty`) and ensure they are accounted for or converted to transactions.

## 3. Definition of Done
- `MONEY_SUPPLY_CHECK` shows `Delta: 0.0000` at Tick 1.
- No direct agent instances are passed to decision or lifecycle logic.
- All asset movements are handled via the `SettlementSystem` or official transaction protocols.
