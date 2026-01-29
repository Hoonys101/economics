# WO-148: 'The Perfect Storm' Stress Test Spec

**Mission**: Introduce a severe, temporary economic shock (supply-side collapse) and verify the system's resilience and the AI government's ability to mitigate the crisis. This test directly targets the interaction between monetary, fiscal, and production systems under extreme duress.

---

## 1. Component: `ShockInjector`

This component is responsible for introducing the supply-side shock at a predetermined point in the simulation.

### 1.1. Interface 명세 (`modules/simulation/api.py`)

```python
from __future__ import annotations
from typing import Protocol, TypedDict

# --- DTOs ---

class ShockConfigDTO(TypedDict):
    """Configuration for the economic shock."""
    shock_start_tick: int
    shock_end_tick: int
    tfp_multiplier: float  # The factor to multiply the baseline TFP by (e.g., 0.5 for a 50% drop)
    baseline_tfp: float   # The normal TFP value to restore to

# --- Interfaces ---

class IShockInjector(Protocol):
    """
    An interface for a component that can inject economic shocks into the simulation.
    It directly manipulates simulation parameters at runtime based on its configuration.
    """
    def __init__(self, config: ShockConfigDTO):
        ...

    def apply(self, current_tick: int) -> None:
        """
        Applies the shock if the simulation is within the shock window.
        This method is expected to be called every tick.
        """
        ...
```

### 1.2. 로직 단계 (Pseudo-code)

The `ShockInjector` will be integrated into the main simulation loop.

```python
class ShockInjector:
    def __init__(self, config: ShockConfigDTO, world: World): # World object provides access to agents/config
        self._config = config
        self._world = world
        self._original_tfp_values = {} # To store pre-shock values

    def apply(self, current_tick: int):
        is_shock_active = self._config["shock_start_tick"] <= current_tick < self._config["shock_end_tick"]

        # AUDIT-AWARE IMPLEMENTATION (TD-142):
        # Target the 'corporate_manager' or equivalent God File that holds production logic.
        corporate_manager = self._world.get_manager("corporate_manager")

        if is_shock_active:
            if not self._original_tfp_values:
                # On first shock tick, save original values
                self._original_tfp_values = corporate_manager.get_all_tfp()
            
            # Apply shock: reduce TFP for all firms
            new_tfp = self._config["baseline_tfp"] * self._config["tfp_multiplier"]
            corporate_manager.set_all_tfp(new_tfp)
        else:
            if self._original_tfp_values:
                # After shock ends, restore original values
                corporate_manager.set_all_tfp(self._config["baseline_tfp"])
                self._original_tfp_values = {} # Clear stored values
```

---

## 2. Component: `StormVerifier`

This component observes the simulation, gathers data, and verifies whether the success metrics were met.

### 2.1. Interface 명세 (`modules/analysis/api.py`)

```python
from __future__ import annotations
from typing import Protocol, TypedDict, List
from simulation.dtos.api import MarketSnapshotDTO

# --- DTOs ---

class StormReportDTO(TypedDict):
    """The final report summarizing the stress test results."""
    zlb_hit: bool
    deficit_spending_triggered: bool
    starvation_rate: float
    peak_debt_to_gdp: float
    volatility_metrics: dict[str, float]
    success: bool
    
class VerificationConfigDTO(TypedDict):
    """Configuration for the verification component."""
    max_starvation_rate: float
    max_debt_to_gdp: float
    # TBD: Define volatility reduction target
```

### 2.2. 로직 단계 (Pseudo-code)

```python
class StormVerifier:
    def __init__(self, config: VerificationConfigDTO, world: World):
        self._config = config
        self._world = world
        self._metrics = {
            "zlb_hit": False,
            "deficit_spending": False,
            "starvation_ticks": 0,
            "total_population_ticks": 0,
            "peak_debt_to_gdp": 0.0
        }

    def update(self, current_tick: int, market_snapshot: MarketSnapshotDTO):
        gov_state = self._world.get_agent_state("government")

        # 1. ZLB Check (Monetary Policy)
        # AUDIT-AWARE IMPLEMENTATION (WO-057): Government has a 30-tick reaction delay.
        # This check will only see a change after the government's action tick.
        if gov_state.monetary_policy.interest_rate < 0.001:
            self._metrics["zlb_hit"] = True

        # 2. Deficit Spending Check (Fiscal Policy)
        if gov_state.spending > gov_state.tax_revenue and current_tick > SHOCK_START_TICK:
            self._metrics["deficit_spending"] = True

        # 3. Debt-to-GDP Check
        debt_to_gdp = gov_state.debt / market_snapshot.gdp if market_snapshot.gdp > 0 else float('inf')
        if debt_to_gdp > self._metrics["peak_debt_to_gdp"]:
            self._metrics["peak_debt_to_gdp"] = debt_to_gdp
            
        # 4. Starvation Rate Check
        # AUDIT-AWARE IMPLEMENTATION (TD-118): Access inventory as a dictionary.
        starving_count = 0
        all_households = self._world.get_all_agent_states("household")
        for hh_state in all_households:
            # The key 'basic_food' must be used, not list iteration.
            food_inventory = hh_state.inventory.get("basic_food", 0.0) 
            if food_inventory < config.STARVATION_THRESHOLD:
                starving_count += 1
        
        self._metrics["starvation_ticks"] += starving_count
        self._metrics["total_population_ticks"] += len(all_households)

    def generate_report(self) -> StormReportDTO:
        final_starvation_rate = self._metrics["starvation_ticks"] / self._metrics["total_population_ticks"]
        
        success = (
            final_starvation_rate < self._config["max_starvation_rate"] and
            self._metrics["peak_debt_to_gdp"] < self._config["max_debt_to_gdp"]
        )
        
        return StormReportDTO(
            zlb_hit=self._metrics["zlb_hit"],
            deficit_spending_triggered=self._metrics["deficit_spending"],
            starvation_rate=final_starvation_rate,
            peak_debt_to_gdp=self._metrics["peak_debt_to_gdp"],
            volatility_metrics={"TBD": 0.0}, # TBD by Team Leader
            success=success
        )
```

---

## 3. 검증 계획 (Verification Plan)

**Primary Success Metrics**:

| Metric | Target | Verification Logic |
| :--- | :--- | :--- |
| **Starvation Rate** | **< 1.0%** | Average percentage of population with sub-threshold 'basic_food' over the simulation run. |
| **Debt-to-GDP Ratio** | **< 200%** | Peak `government.debt / market.gdp` ratio observed after the shock. |
| **Volatility Reduction** | **50%** | **TBD (Team Leader Review)**. Proposal: Compare GDP standard deviation during the crisis (tick 100-160) with and without the AI government's policy response. |

**Verification Script**: A new script `scripts/run_stress_test_wo148.py` will be created.

**AUDIT-AWARE IMPLEMENTATION (`TD-122`):** To avoid conflicts with the disorganized test suite, this will be a standalone execution script, not a `pytest` test.

```python
# scripts/run_stress_test_wo148.py (Pseudo-code)

def main():
    # 1. Load a stable, pre-shock baseline configuration from Phase 23.
    config = ConfigFactory.load("phase23_golden_age")

    # 2. Setup the shock and verifier
    shock_config = ShockConfigDTO(
        shock_start_tick=100,
        shock_end_tick=130,
        tfp_multiplier=0.5, # 3.0 -> 1.5
        baseline_tfp=3.0
    )
    
    # 3. Initialize simulation with injector and verifier
    world = World(config)
    injector = ShockInjector(shock_config, world)
    verifier = StormVerifier(...)
    
    # 4. Run simulation
    for tick in range(200):
        injector.apply(tick)
        world.tick()
        verifier.update(tick, world.get_market_snapshot())

    # 5. Generate and assert report
    report = verifier.generate_report()
    print(report)
    assert report["success"], "The Perfect Storm stress test failed."

if __name__ == "__main__":
    main()
```

---

## 4. 🚨 Risk & Impact Audit (기술적 위험 분석)

*   **Constraint (God Files)**: Implementation requires direct interaction with complex, low-cohesion modules (`corporate_manager.py`, `ai_driven_household_engine.py`) as identified in **TD-140, TD-141, TD-142**.
    *   **Mitigation**: The `ShockInjector` logic must be surgically precise. It will modify TFP via a dedicated `corporate_manager.set_all_tfp()` method. The `StormVerifier` will query household state via read-only DTOs, minimizing side effects.

*   **Risk (DTO Contract Mismatch)**: The starvation metric calculation is highly likely to fail if it adheres to the formal `List[GoodsDTO]` contract for `HouseholdStateDTO.inventory`.
    *   **Mitigation (MANDATORY)**: As per **TD-118**, the implementation **MUST** access the inventory as a dictionary (`household.inventory.get("basic_food", 0.0)`). This is a temporary workaround to ensure test functionality pending the resolution of `TD-118`.

*   **Constraint (Policy Reaction Time)**: The AI government's policy response is limited to a single action during the 30-tick crisis window, as per the `GOV_ACTION_INTERVAL` in **WO-057**.
    *   **Mitigation**: The verification plan must not assume a continuous government response. The success of the test hinges on the effectiveness of this *single* fiscal and monetary adjustment.

*   **Risk (Test Infrastructure)**: The project's test suite is currently unstable (**TD-122**) and a related stress test config is pending (**TD-007**).
    *   **Mitigation**: This Work Order will be validated via a dedicated, self-contained script (`scripts/run_stress_test_wo148.py`) to ensure isolation from the unstable test environment.

---

## 5. [Routine] Mandatory Reporting

**Jules Implementation Note**: Upon completion, any insights gained (e.g., unexpected system behavior, performance bottlenecks) or new technical debt incurred during the implementation of `WO-148` must be documented in `communications/insights/WO-148.md`. This is a strict requirement to prevent tribal knowledge and ensure project transparency.
