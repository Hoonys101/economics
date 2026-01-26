# Spec: TRACK_ALPHA - Monetary Initialization & Leak Hunt

**Version:** 1.0
**Author:** Gemini (Scribe)
**Date:** 2026-01-26
**Related Tickets:** TD-111, TD-115

---

## 1. Problem Statement

An initial money supply leak of **-99,680** is observed at Tick 1. The pre-flight audit confirms this is an architectural issue stemming from the simulation's initialization sequence:
1.  **Incorrect Baseline Calculation Timing**: `SimulationInitializer` calculates the baseline M2 money supply *after* executing methods (`Bootstrapper.inject_initial_liquidity`, `agent.update_needs`) that transfer funds to the `EconomicRefluxSystem`.
2.  **Flawed M2 Definition**: The M2 calculation logic in `EconomicIndicatorTracker` intentionally excludes the `EconomicRefluxSystem`'s balance. Any funds moved into the reflux system during initialization are thus treated as a "leak" from the baseline.
3.  **SRP Violation**: The definition of a core financial aggregate (M2) resides within a metrics tracking module (`EconomicIndicatorTracker`), violating the Single Responsibility Principle and creating a risk of inconsistent definitions, as `world_state.calculate_total_money()` is used elsewhere.

This specification details the necessary refactoring to ensure Zero-Sum financial integrity from Tick 0.

## 2. Design & Implementation Plan

The solution is a three-pronged approach: centralize the M2 definition, correct the initialization order, and integrate the new system for consistent tracking.

### Track A: Centralize M2 Money Supply Definition (SRP Fix)

To create a single source of truth for money supply, we will move the calculation logic to the `EconomicRefluxSystem`, which is at the center of the accounting discrepancy.

#### 1. `modules/finance/api.py` (New File)

A new interface will be created to formalize the contract for providing money supply data.

```python
# modules/finance/api.py
from __future__ import annotations
from typing import Protocol, TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from simulation.world_state import WorldState

class IMoneySupplyProvider(Protocol):
    """
    An interface for objects that can provide authoritative calculations
    of the simulation's money supply.
    """
    @staticmethod
    def get_m2_money_supply(world_state: WorldState) -> Tuple[float, float]:
        """
        Calculates the M2 money supply and the balance of the reflux system.

        Args:
            world_state: The complete state of the simulation world.

        Returns:
            A tuple containing:
            - The total M2 money supply (including reflux balance).
            - The balance of the EconomicRefluxSystem.
        """
        ...
```

#### 2. `simulation/systems/reflux_system.py` (Modification)

The `EconomicRefluxSystem` will implement the `IMoneySupplyProvider` interface, becoming the authoritative source for M2 calculations.

```python
# In simulation/systems/reflux_system.py
from typing import List, Optional, Tuple
import logging
from modules.finance.api import IFinancialEntity, InsufficientFundsError, IMoneySupplyProvider

# Add TYPE_CHECKING import for WorldState
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class EconomicRefluxSystem(IFinancialEntity, IMoneySupplyProvider):
    # ... existing __init__, id, assets, deposit, withdraw, capture methods ...

    # ... existing distribute method ...

    @staticmethod
    def get_m2_money_supply(world_state: 'WorldState') -> Tuple[float, float]:
        """
        Calculates the authoritative M2 money supply for the entire simulation.
        M2 is defined as the sum of all assets held by households, firms, the bank,
        the government, and the EconomicRefluxSystem itself.

        Args:
            world_state: The complete state of the simulation world.

        Returns:
            A tuple containing:
            - The total M2 money supply.
            - The balance of the EconomicRefluxSystem.
        """
        total_m2 = 0.0

        # 1. Households
        total_m2 += sum(h.assets for h in world_state.households if getattr(h, "is_active", True))

        # 2. Firms
        total_m2 += sum(f.assets for f in world_state.firms if getattr(f, "is_active", False))

        # 3. Bank Reserves
        if world_state.bank:
            total_m2 += world_state.bank.assets

        # 4. Government Assets
        if world_state.government:
            total_m2 += world_state.government.assets
        
        # 5. Reflux System's own balance
        reflux_balance = world_state.reflux_system.balance if world_state.reflux_system else 0.0
        total_m2 += reflux_balance

        return total_m2, reflux_balance

```

### Track B: Correct Initialization Order

The core of the leak fix is to re-sequence the `SimulationInitializer` to capture the financial baseline *before* any economic activities can occur.

#### 1. `simulation/initialization/initializer.py` (Modification)

The baseline calculation will be moved to a point immediately after all agents are created and endowed with initial assets, but before any system-level processes run.

```python
# In simulation/initialization/initializer.py, inside build_simulation()

# ... (Code to create sim, settlement_system, households, firms, agents) ...
# ... (Code to create bank, government, and set government on bank) ...
# ... (Code to create tracker, central_bank, finance_system) ...
# ... (Code to create real_estate_units and assign to top households) ...

        # --- TRACK ALPHA: BASELINE MONEY SUPPLY CALCULATION ---
        # Establish the baseline money supply AFTER all agents and initial assets
        # are created, but BEFORE any economic activity (bootstrapping, needs) occurs.
        # This is the authoritative snapshot of the simulation's initial wealth.
        # We now call the centralized M2 calculation method.
        # Note: sim.world_state is available on the 'sim' object.
        m2_baseline, reflux_baseline = EconomicRefluxSystem.get_m2_money_supply(sim.world_state)
        sim.world_state.baseline_money_supply = m2_baseline
        sim.world_state.baseline_reflux_balance = reflux_baseline # Store for verification
        self.logger.info(
            f"INITIAL_MONEY_SUPPLY | Baseline M2 established: {m2_baseline:,.2f} "
            f"(Initial Reflux Balance: {reflux_baseline:,.2f})",
            extra={"tags": ["init", "money_supply"]}
        )
        # --- END TRACK ALPHA MODIFICATION ---


        sim.markets: Dict[str, Market] = { ... } # Market creation proceeds
        # ... (rest of market creation) ...

        # Phase 22.5 & WO-058: Bootstrap firms BEFORE first update_needs call
        # These actions, which can transfer money, now happen AFTER the baseline is set.
        Bootstrapper.inject_initial_liquidity(sim.firms, self.config)
        Bootstrapper.force_assign_workers(sim.firms, sim.households)

        for agent in sim.households + sim.firms:
            agent.update_needs(sim.time)
            # ... (rest of agent setup) ...
        
        # ... (rest of the build_simulation method, REMOVING the old baseline calculation at the end) ...

        # Find and DELETE the following lines from the end of the method:
        # sim.world_state.baseline_money_supply = sim.world_state.calculate_total_money()
        # self.logger.info(f"Initial baseline money supply established: {sim.world_state.baseline_money_supply:,.2f}")
```

### Track C: Integrate and Verify

Finally, update the `EconomicIndicatorTracker` to use the new, centralized M2 provider.

#### 1. `simulation/metrics/economic_tracker.py` (Modification)

The tracker will be refactored to consume the new API, ensuring consistent reporting.

```python
# In simulation/metrics/economic_tracker.py
# ... (imports)
# Add the new centralized provider
from simulation.systems.reflux_system import EconomicRefluxSystem 

class EconomicIndicatorTracker:
    # ... (existing __init__ and other properties) ...

    def track(
        self,
        time: int,
        households: List[Household],
        firms: List[Firm],
        markets: Dict[str, Market],
        world_state: 'WorldState', # Add world_state as an argument
    ) -> None:
        """Calculates and records economic indicators for the current tick."""
        self.logger.debug(...)
        record: Dict[str, Any] = {"time": time}

        # --- TRACK ALPHA: USE CENTRALIZED M2 PROVIDER ---
        # The 'money_supply' argument is now deprecated.
        # We get M2 directly from the authoritative source using the world_state.
        m2_supply, reflux_balance = EconomicRefluxSystem.get_m2_money_supply(world_state)
        record["money_supply"] = m2_supply
        record["reflux_balance"] = reflux_balance # Track as a separate metric for analysis
        # --- END TRACK ALPHA MODIFICATION ---

        # ... (rest of the tracking logic) ...
        # The logic that previously calculated money_supply_m1 can be removed or refactored
        # as the canonical value is now provided.

        # Find and remove the old M2 calculation:
        # money_supply_m1 = total_household_assets + total_firm_assets
        # record["money_supply"] = money_supply_m1
        
        # ... (rest of the method) ...

    # DELETE the entire get_m2_money_supply method from this file.
    # def get_m2_money_supply(self, world_state: 'WorldState') -> float:
    #     ... (DELETE THIS)
```

## 3. Verification Plan

1.  **Unit Tests**: Existing unit tests for `SimulationInitializer` might require updates due to the changed sequence.
2.  **Integration Test**:
    *   Run a full simulation for at least 2 ticks.
    *   **Verify Log Output**: Confirm the presence of the `INITIAL_MONEY_SUPPLY` log message at initialization with the correct baseline M2 and a reflux balance of 0.0.
    *   **Verify Zero-Sum at Tick 1**: Execute `scripts/audit_zero_sum.py` (or equivalent verification script). The script should report a delta of `0.0` between the baseline M2 and the calculated M2 at Tick 1, confirming the leak (TD-115) is resolved.
3.  **Test Fixture Regeneration**:
    *   **Acknowledge Impact**: This change WILL alter the initial state of the simulation. All test fixtures relying on `GoldenLoader` are now invalid.
    *   **Action Required**: After merging this fix, a dedicated task must be undertaken to regenerate all golden-path test fixtures using the new, correct baseline.

## 4. 🚨 Risk & Impact Audit (Summary)

This design directly addresses the risks identified in the pre-flight audit:

-   **Monolithic Initializer**: The change is surgically targeted to reorder a single critical step, minimizing disruption to the coupled `initializer.py` logic.
-   **Ambiguous Money Supply Definition**: The SRP violation is resolved by creating a single, authoritative `IMoneySupplyProvider` implementation, eliminating the dual-definition problem.
-   **Initialization-Phase Leak**: The leak is patched by definition. The baseline is captured *before* fund-transferring activities, and the M2 calculation is corrected to be fully inclusive, ensuring conservation of money.
-   **Invalidation of Test Fixtures**: The plan explicitly acknowledges that all golden fixtures will require regeneration post-merge. This is a necessary and accepted consequence of fixing a foundational architectural flaw.

---
## 5. Jules Reporting Mandate
**Routine Task**: During implementation, any new insights, potential optimizations, or discovered technical debt related to the initialization process must be logged in a new markdown file in `communications/insights/` for review. The filename should be `insight_track_alpha_<description>.md`.
