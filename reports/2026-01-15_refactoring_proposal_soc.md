# Refactoring Proposal: Separation of Concerns (SoC) for God Classes

**Date:** 2026-01-15
**Author:** Jules (AI Software Engineer)
**Target:** Core Simulation Architecture

---

## 1. Executive Summary

This report identifies several "God Classes" within the codebase that violate the Separation of Concerns (SoC) principle. These classes have accumulated excessive responsibilities, making the system difficult to test, maintain, and extend.

The primary recommendation is to decompose these monolithic classes into smaller, focused components using the Strategy, Component, or Delegate patterns.

## 2. Identified God Classes

Based on static analysis (lines of code, number of methods, import density) and logic review, the following classes are flagged:

### 2.1. `Simulation` (in `simulation/engine.py`)
*   **Status:** Critical (1337 lines)
*   **Current Responsibilities:**
    *   **Orchestration:** Manages the main simulation loop (`run_tick`).
    *   **Initialization:** Creates and wires all agents, markets, and systems.
    *   **Data Collection:** Directly manages `EconomicIndicatorTracker` and buffers data.
    *   **State Management:** Handles transaction processing, agent lifecycle (death/liquidation), and market clearing.
    *   **Domain Logic Leakage:** Contains specific logic for "Chaos Events", "Gold Standard Verification", and "Social Rank Updates".
*   **SoC Violation:** The engine knows *too much* about the internal workings of every subsystem.

### 2.2. `Household` (in `simulation/core_agents.py`)
*   **Status:** High (1106 lines)
*   **Current Responsibilities:**
    *   **Economic Actor:** Consumes goods, supplies labor, manages assets.
    *   **Demographic Entity:** Ages, reproduces, dies, tracks genealogy.
    *   **Psychological Agent:** Manages personality, happiness, stress, and political opinions.
    *   **Social Actor:** Tracks social status, housing tiers, and conformity.
    *   **Decision Making:** While it uses a `DecisionEngine`, the `Household` class still contains heavy logic for "Shadow Wages", "Housing Decisions", and "Leisure Effects".
*   **SoC Violation:** Mixing biological/demographic state with economic transactional logic and high-level cognitive processes.

### 2.3. `Firm` (in `simulation/firms.py`)
*   **Status:** Moderate/High (860 lines)
*   **Current Responsibilities:**
    *   **Production:** Calculates output via Cobb-Douglas (including automation/inputs).
    *   **Finance:** Manages assets, loans, bankruptcy, dividends, and stock issuance.
    *   **Human Resources:** Hiring, firing, payroll (though partially delegated to `HRDepartment`).
    *   **Marketing:** Brand awareness updates, marketing budget optimization.
    *   **Strategy:** System 2 planning and inventory management.
*   **SoC Violation:** Although some components (`HRDepartment`, `FinanceDepartment`) exist, the main class still tightly couples production physics with financial strategy and market interaction.

---

## 3. Refactoring Proposals

### 3.1. Refactoring `Simulation` Class

**Strategy:** Extract specialized managers to handle specific subsystems, leaving `Simulation` as a lightweight facade/coordinator.

*   **Proposal A: Extract `SimulationInitializer` (Builder Pattern)**
    *   Move the massive `__init__` logic, agent creation, and wiring into a dedicated builder class.
    *   *Benefit:* Simplifies the engine's startup code and allows for different simulation configurations (e.g., testing vs. production).

*   **Proposal B: Extract `CycleManager` or `PhaseOrchestrator`**
    *   The `run_tick` method is too long. Group related steps (e.g., "Agent Update Phase", "Market Clearing Phase", "Reporting Phase") into a `PhaseOrchestrator`.
    *   *Benefit:* Makes the main loop readable and declarative.

*   **Proposal C: Extract `LifecycleManager`**
    *   Move `_handle_agent_lifecycle` (Death, Liquidation, Inheritance) to a dedicated `LifecycleManager`.
    *   *Benefit:* Centralizes complex cleanup logic (which involves multiple systems) away from the main loop.

### 3.2. Refactoring `Household` Class

**Strategy:** Component-based Architecture. The `Household` class should become a container for specific behaviors.

*   **Proposal A: `DemographicsComponent`**
    *   Encapsulate `age`, `gender`, `children_ids`, `spouse_id`, `death`, and `aging` logic.
    *   *Benefit:* Decouples biological lifecycle from economic behavior.

*   **Proposal B: `EconomyComponent` (or `Wallet`)**
    *   Encapsulate `assets`, `inventory`, `transactions`, `income_tracking`, and `portfolio`.
    *   *Benefit:* Centralizes financial state, making it easier to track "money leaks" (WO-056).

*   **Proposal C: `LaborComponent`**
    *   Encapsulate `labor_skill`, `talent`, `employment_status`, `job_search`, and `shadow_wage` logic.
    *   *Benefit:* Isolates the complex logic of skill growth and wage negotiation.

### 3.3. Refactoring `Firm` Class

**Strategy:** Continue the existing pattern of Departmentalization.

*   **Proposal A: `ProductionDepartment`**
    *   Extract `produce()`, `input_inventory`, `technology_manager` interaction, and `automation_level` into a dedicated component.
    *   *Benefit:* Separates "physics" (production function) from "business" (money).

*   **Proposal B: `SalesDepartment` (or `MarketingDepartment`)**
    *   Move `post_ask`, `brand_manager`, `marketing_budget`, and `calculate_brand_premium` into a component.
    *   *Benefit:* Encapsulates the logic of how the firm faces the market.

---

## 4. Implementation Roadmap (Phased Approach)

To avoid breaking the simulation, refactoring should be gradual:

1.  **Phase 1 (Low Risk):** Extract `LifecycleManager` from `Simulation`. This logic is self-contained at the end of the tick.
2.  **Phase 2 (Medium Risk):** Refactor `Household` into components (`Demographics`, `Labor`). This requires updating many references in the tests and engine.
3.  **Phase 3 (High Risk):** Extract `ProductionDepartment` from `Firm`. This touches the core revenue loop.

## 5. Conclusion

Addressing these God Classes is crucial for the stability of the simulation, particularly for resolving complex bugs like the "Money Leak" (WO-056) and "Zombie Economy". By isolating concerns, we can write targeted unit tests that verify specific behaviors (e.g., "Does the Labor Component correctly decay wages?") without spinning up the entire engine.
