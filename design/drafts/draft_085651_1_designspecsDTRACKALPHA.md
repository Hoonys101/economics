# Analysis Report: Track Alpha & DTO Purity Recovery

**Date:** 2026-01-27
**Author:** Gemini Administrative Assistant

## 1. Executive Summary

This report details the findings of a forensic analysis into two critical technical debts: **TD-115 (Asset Leak)** and **TD-117 (DTO Purity Gate Regression)**. The root causes for both issues have been identified in the simulation's initialization and demographic management systems.

-   **TD-115 Root Cause:** The asset leak of **-99,680** is caused by the simulation's accounting baseline (`WorldState.baseline_money_supply`) being recorded *after* agent-level financial activities have already occurred during the initialization sequence.
-   **TD-117 Root Cause:** The DTO Purity Gate regression stems from two primary sources: direct agent state manipulation within the `DemographicManager` during child birth, and the passing of direct agent instances (`self`) into the `LifecycleContext` within `Household.update_needs`.

## 2. TD-115: Asset Leak Analysis (-99,680)

### 2.1. Forensic Findings

The investigation, guided by `design/specs/D_TRACK_ALPHA_REMEDIATION.md`, confirms the leak occurs during the simulation's startup phase at Tick 0. The issue is not a flaw in zero-sum calculations but a flaw in the *timing* of the initial accounting.

The sequence of operations in `simulation/initialization/initializer.py:build_simulation` is as follows:

1.  `Bootstrapper.inject_initial_liquidity(...)`: All initial money is created and distributed to firms.
2.  `Bootstrapper.force_assign_workers(...)`: Agents are assigned roles. This may involve transactions.
3.  `agent.update_needs(...)`: This method is called for all agents. This is a primary suspect for triggering initial consumption, spending, or other financial decisions based on the agent's newly created state.
4.  **(Many other steps)**
5.  `sim.world_state.baseline_money_supply = sim.world_state.calculate_total_money()`: **This is the critical flaw.** The baseline is recorded at the very end of the initialization process.

Any financial transaction that occurs in steps 2 or 3 (or any subsequent step before the baseline is recorded) will reduce the total amount of money in the system from its intended starting value. When `calculate_total_money()` is finally called, it correctly reports the *new, lower total*. This discrepancy manifests as the "-99,680" asset leak.

### 2.2. Location of Flaw

-   **File:** `simulation/initialization/initializer.py`
-   **Method:** `build_simulation`
-   **Specific Issue:** The call to set `sim.world_state.baseline_money_supply` occurs at the end of the method, after multiple functions that can (and do) trigger agent financial activity have already been executed.

### 2.3. Remediation Recommendation

The `baseline_money_supply` must be recorded immediately after the initial liquidity is injected and before any agent-driven logic is executed. The `build_simulation` method should be re-ordered to capture the baseline at the correct moment.

## 3. TD-117: DTO Purity Gate Regression Analysis

### 3.1. Forensic Findings

The DTO Purity principle, as defined in `design/specs/DTO_PURITY_GATE_SPEC.md`, is intended to prevent decision engines and other systems from directly accessing or modifying an agent's internal state. The analysis confirms this principle has been violated, leading to a regression.

### 3.2. Location of Flaws

#### Flaw 1: Direct State Manipulation in `DemographicManager`

The most severe violation occurs during the birth process.

-   **File:** `simulation/systems/demographic_manager.py`
-   **Method:** `process_births`
-   **Specific Issue:** The manager directly subtracts assets from the parent agent to provide an initial gift to the child, bypassing all standard transaction and settlement protocols. It calls a protected method directly on the agent instance.

    ```python
    # In process_births:
    initial_gift = max(0.0, min(parent.assets * 0.1, parent.assets))
    parent._sub_assets(initial_gift) // VIOLATION: Direct state modification
    ```

    This creates tight coupling and makes the system's monetary flow difficult to track and verify. A failure in this block could lead to an asset leak, which is why a manual `try...except` block with a rollback (`parent._add_assets`) was added, further compounding the anti-pattern.

#### Flaw 2: Impure `LifecycleContext` in `Household.update_needs`

The second violation occurs when preparing the context for lifecycle updates.

-   **File:** `simulation/core_agents.py`
-   **Method:** `update_needs`
-   **Specific Issue:** The method creates a `LifecycleContext` dictionary and passes the entire household instance (`self`) into it. This context is then passed to `self.bio_component.run_lifecycle`, giving the `BioComponent` and any downstream logic full, unrestricted access to the agent's internal state and methods.

    ```python
    # In Household.update_needs:
    context: LifecycleContext = {
        "household": self, # VIOLATION: Passing direct agent instance
        "market_data": market_data if market_data else {},
        "time": current_tick
    }
    self.bio_component.run_lifecycle(context)
    ```
    The comment `Some lifecycle logic might still need 'self' to access properties` explicitly confirms awareness of this design flaw.

### 3.3. Status of `RuleBasedHouseholdDecisionEngine`

The investigation confirms that `simulation/decisions/rule_based_household_engine.py` **is compliant** with the DTO Purity Gate. It correctly operates on the `state` and `config` DTOs provided in the `DecisionContext`. The regression does not lie within the decision engine itself, but in the surrounding systems that fail to adhere to the same data-contract principles.
