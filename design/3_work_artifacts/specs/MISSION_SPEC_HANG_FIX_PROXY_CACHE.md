# Design Document: WO-SPEC-HANG-FIX-PROXY-CACHE (Phase A - Proxy Cache in Initializer)

## 1. Introduction

- **Purpose**: Optimize the `_init_phase4_population` method in `SimulationInitializer` to prevent excessive `Simulation.__getattr__` proxy calls during agent registration loops, which causes significant initialization delays (10,000+ unnecessary calls).
- **Scope**: Modifications are strictly limited to `simulation/initialization/initializer.py`, specifically the `_init_phase4_population` method.
- **Goals**: 
  - Cache `sim.bank`, `sim.settlement_system`, and `sim.demographic_manager` as local variables before entering the agent loops.
  - Replace all `sim.X` attribute accesses inside the household and firm registration loops with these local variables.
  - Reduce initialization time by minimizing proxy `__getattr__` overhead.

## 2. System Architecture & API Impact

- **API Changes**: None. No new DTOs or DAOs are required. The interface of `SimulationInitializer` remains identical.
- **DTO Definitions**: N/A
- **DAO Interfaces**: N/A
- **Exception Handling**: No new exception types are introduced. Existing exceptions (e.g., if a system is uninitialized) will naturally raise `AttributeError` or `ValueError` as before, but sooner (during local caching).

## 3. Detailed Design (Pseudo-code)

### 3.1. `SimulationInitializer._init_phase4_population`

```python
def _init_phase4_population(self, sim: Simulation) -> None:
    """
    Phase 4: Atomic Registration & Population Injection
    """
    sim.agent_registry.households = self.households
    sim.agent_registry.firms = self.firms
    sim.goods_data = self.goods_data

    # Ensure sim.agents is initialized
    if not sim.agents:
        sim.agents = {}

    # --- NEW: Cache frequently accessed attributes as local variables ---
    # This prevents 10,000+ Simulation.__getattr__ proxy calls
    agents_local = sim.agents
    agent_registry_local = sim.agent_registry
    settlement_system_local = sim.settlement_system
    bank_id_local = sim.bank.id
    demographic_manager_local = getattr(sim, 'demographic_manager', None)

    # 1. Household Atomic Registration
    for hh in sim.households:
        agents_local[hh.id] = hh
        agent_registry_local.register(hh)

        # Guarantee Settlement Account Existence
        settlement_system_local.register_account(bank_id_local, hh.id)
        hh.settlement_system = settlement_system_local

        if demographic_manager_local and hasattr(hh, 'demographic_manager'):
            hh.demographic_manager = demographic_manager_local

    # 2. Firm Atomic Registration
    for firm in sim.firms:
        agents_local[firm.id] = firm
        agent_registry_local.register(firm)

        # Guarantee Settlement Account Existence BEFORE Bootstrapper
        settlement_system_local.register_account(bank_id_local, firm.id)
        firm.settlement_system = settlement_system_local

    # Determine next available ID
    max_user_id = 0
    if agents_local:
        int_keys = [k for k in agents_local.keys() if isinstance(k, int)]
        max_user_id = max(int_keys) if int_keys else 0
    sim.next_agent_id = max(100, max_user_id + 1)

    if demographic_manager_local:
        demographic_manager_local.sync_stats(sim.households)
        demographic_manager_local.set_world_state(sim.world_state)

    # Distribute Real Estate
    top_20_count = len(sim.households) // 5
    top_households = sorted(sim.households, key=lambda h: h.get_balance(DEFAULT_CURRENCY), reverse=True)[:top_20_count]
    for i, hh in enumerate(top_households):
        if i < len(sim.real_estate_units):
            unit = sim.real_estate_units[i]
            unit.owner_id = hh.id
            hh._econ_state.owned_properties.append(unit.id)
            unit.occupant_id = hh.id
            hh._econ_state.residing_property_id = unit.id
            hh._econ_state.is_homeless = False

    self.logger.info(f"Phase 4 Complete: Registered {len(sim.households)} Households and {len(sim.firms)} Firms atomically.")
```

## 4. 🚨 [Debt Review] Mandatory Ledger Audit

- **Analysis of `TECH_DEBT_LEDGER.md`**: 
  - This optimization directly aligns with resolving performance debts similar to `TD-PERF-GETATTR-LOOP` (where getattr bottlenecks in tight loops crippled performance).
  - This change will **resolve** a silent, unrecorded technical debt where God Class proxies (`Simulation.__getattr__` mapping to `WorldState`) generate significant overhead in heavily iterated startup phases.
  - The change strictly enforces safe reference handling and will not exacerbate any existing debt.

## 5. 🚨 Risk & Impact Audit (Pre-Implementation Risk Analysis)

- **DTO/DAO Interface Impact**: None. The object structures and properties remain the same.
- **Circular Reference Risk**: None. We are merely creating local variable bindings for objects that are already instantiated and safely stored.
- **Test Impact**: 
  - **Negligible impact on logic**. Existing mock-based initialization tests (`tests/initialization/test_initializer.py`) must ensure `sim.bank`, `sim.settlement_system`, and `sim.demographic_manager` are properly configured *before* phase 4, which is currently standard behavior.
  - **Evaluation Timing**: In the legacy code, `sim.bank.id` was evaluated inside the loop. In the optimized code, it's evaluated immediately prior to the loop. If `sim.bank` was `None` at Phase 4 execution, both variants would fail, making this a transparent optimization.
- **Settings Dependency**: No configuration files are impacted.
- **Pre-requisite Tasks**: None.

## 6. 🚨 [Conceptual Debt] (정합성 부채)

- **Registry Aliasing Risk**: Caching `sim.agents` into `agents_local` implies that no internal mechanism within `agent_registry_local.register()` reassigns the `sim.agents` dictionary pointer entirely. Based on the `IAgentRegistry` architecture, registration alters internal list contents, not the `sim.agents` reference itself, meaning this is a safe, negligible risk.

## 7. Testing & Verification Strategy

- **Integration Check**: Run standard initialization tests to verify no `AttributeError` or reference loss occurs.
- **Performance Benchmark**: Run a full simulation bootstrap with $N=10,000$ households to confirm a noticeable drop in the time taken specifically by `_init_phase4_population`.
- **Mocking Guide**:
  - **Required**: Mocks of `Simulation` passed to `_init_phase4_population` must have `bank`, `settlement_system`, and `demographic_manager` properties pre-populated as standard objects, not dynamically resolved lambda mocks.
  - **Avoid**: Do not return `MagicMock()` for `sim.agents` if it expects dictionary modification. Provide a real Python `dict`.

## 8. 🚨 Mandatory Reporting Instruction

**Attention Jules**:
During or after the implementation of this specification, you **MUST** record any insights or discovered technical debt in a standalone markdown file.

**Instruction**: Create the file `communications/insights/WO-SPEC-HANG-FIX-PROXY-CACHE.md` and document any hidden performance bottlenecks, proxy resolution risks, or GC pause potential you observe while investigating the `Simulation` and `WorldState` instantiation process. Failure to create this report file will result in a Hard-Fail for the mission.