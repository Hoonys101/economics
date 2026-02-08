# Refactoring Proposal: Separation of Concerns (SoC) & God Class Elimination

**Date:** 2026-01-13
**Author:** Jules (AI Software Engineer)
**Target:** `simulation/` codebase

## 1. Executive Summary

This report identifies classes within the simulation codebase that violate the **Separation of Concerns (SoC)** principle and exhibit "God Class" anti-patterns. A "God Class" is an object that controls too many distinct aspects of the system, leading to high coupling, low cohesion, and difficult maintenance.

Our analysis highlights the `Simulation` engine and the core agents (`Household`, `Firm`) as the primary candidates for refactoring. We propose a component-based decomposition strategy to improve modularity and testability.

## 2. Identified God Classes

### A. The Orchestrator: `Simulation` (`simulation/engine.py`)
**Diagnosis:** Critical
The `Simulation` class handles initialization, the main time-step loop, transaction processing coordination, market clearing triggers, data collection, *and* specific domain logic (e.g., chaos events, social rank calculation).

**Symptoms:**
*   **Excessive Responsibilities:** It manages the lifecycle of every subsystem (Bank, Markets, AI, Government, Demographics).
*   **Bloated `run_tick`:** The main loop explicitly calls dozens of disjointed sub-systems, making the flow hard to follow.
*   **Data Preparation Logic:** The `_prepare_market_data` method contains complex logic for aggregating market signals, which should belong to a sensory or data system.
*   **Domain Logic Leakage:** Calculations like `_update_social_ranks` and `_calculate_reference_standard` (Social Physics) and chaos injection (Event System) are hardcoded into the engine.

### B. The Monolith Agent: `Household` (`simulation/core_agents.py`)
**Diagnosis:** High
The `Household` class acts as a container for biological, economic, psychological, and social state. While some logic is delegated (e.g., `LeisureManager`), the main class still orchestrates too much low-level behavior.

**Symptoms:**
*   **Mixed Domains:** A single class tracks `education_xp` (Learning), `inventory` (Economics), `conformity` (Psychology), and `children_ids` (Biology).
*   **Complex Consumption:** The `consume` method handles durable goods logic, service consumption, and utility calculation all in one place.
*   **Internal Decision Logic:** Methods like `choose_best_seller` and `decide_housing` contain business logic that belongs in specialized decision components.

### C. The Industrial Giant: `Firm` (`simulation/firms.py`)
**Diagnosis:** Moderate to High
Although `Firm` has delegated HR and Finance to departments, it still retains heavy logic for production physics and marketing strategy.

**Symptoms:**
*   **Production Physics:** The `produce` method contains raw Cobb-Douglas equations, automation decay math, and input constraint logic.
*   **Marketing & Pricing:** Logic for `post_ask` (brand stamping) and `_calculate_invisible_hand_price` (shadow pricing) resides directly in the agent.

### D. The State Machine: `Government` (`simulation/agents/government.py`)
**Diagnosis:** Moderate
The `Government` class mixes tax calculation rules, welfare distribution execution, and specialized systems like Public Education.

**Symptoms:**
*   **Feature Creep:** The `run_public_education` method directly implements scholarship logic inside the agent.
*   **Policy Logic:** Manual implementation of Taylor Rule calculations (for shadow logging) inside `make_policy_decision`.

---

## 3. Refactoring Proposals

### Proposal 1: Decompose `Simulation` Engine

**Goal:** Transform `Simulation` into a lightweight coordinator that delegates to specialized Systems.

*   **Extract `MarketOrchestrator`:**
    *   **Responsibility:** Handling `clear_orders`, `match_orders` loops, and triggering `stock_market` updates.
    *   **Benefit:** Removes the market looping logic from `run_tick`.
*   **Extract `SensorySystem` (or `DataCollector`):**
    *   **Responsibility:** Move `_prepare_market_data` and `tracker` updates here. This system gathers world state and packages it for agents.
    *   **Benefit:** Clean separation between "What happened" and "What agents see".
*   **Extract `SocialPhysicsSystem`:**
    *   **Responsibility:** Move `_update_social_ranks` and `_calculate_reference_standard` here.
    *   **Benefit:** Social dynamics become a pluggable module.
*   **Refine `EventSystem`:**
    *   **Responsibility:** Move Chaos Injection logic out of `run_tick` into a configurable event manager.

### Proposal 2: Componentize `Household`

**Goal:** Move towards an Entity-Component (Composition over Inheritance) style.

*   **Extract `BioComponent`:**
    *   **Attributes:** `age`, `gender`, `children_ids`, `parent_id`, `death_tick`.
    *   **Logic:** Aging, reproduction eligibility.
*   **Extract `EconomyComponent`:**
    *   **Attributes:** `assets`, `inventory`, `portfolio`, `durable_assets`.
    *   **Logic:** `consume` (inventory management), `update_needs` (via ConsumptionBehavior).
*   **Extract `SocialComponent`:**
    *   **Attributes:** `social_rank`, `conformity`, `political_opinion`.
    *   **Logic:** `update_political_opinion`, `calculate_social_status`.

### Proposal 3: Streamline `Firm`

**Goal:** Complete the Departmentalization started with HR and Finance.

*   **Extract `ProductionDepartment`:**
    *   **Responsibility:** Encapsulate the `produce()` method. Handle Input/Output inventory constraints, Technology multipliers, and Automation decay.
*   **Extract `MarketingDepartment`:**
    *   **Responsibility:** Move `brand_manager`, `marketing_budget` logic, `post_ask` (selling), and `pricing_strategy` here.

### Proposal 4: Modularize `Government`

**Goal:** Separate Policy *Rules* from Agent *Execution*.

*   **Extract `MinistryOfEducation`:**
    *   **Responsibility:** Encapsulate `run_public_education`. The Government agent just funds it.
*   **Extract `TaxAgency`:**
    *   **Responsibility:** Encapsulate `calculate_income_tax`, `calculate_corporate_tax`, and bracket logic.

---

## 4. Implementation Roadmap

1.  **Phase 1: Engine Detox (High Impact)**
    *   Refactor `_prepare_market_data` into a standalone `MarketDataAggregator`.
    *   Move Social Rank logic to `SocialSystem`.
2.  **Phase 2: Firm Departments (Low Risk)**
    *   Extract `ProductionDepartment`.
    *   Move `produce()` logic.
3.  **Phase 3: Household Decomposition (High Effort)**
    *   Start by grouping attributes into Data Classes (`HouseholdBio`, `HouseholdEconomy`).
    *   Gradually move methods to these components.
4.  **Phase 4: Government Ministries**
    *   Extract Education logic.

## 5. Conclusion

By adopting these changes, the codebase will move from a "God Object" architecture to a "System-Component" architecture. This will make unit testing significantly easier (testing `ProductionDepartment` in isolation without mocking a whole `Firm` and `Market`) and allow for more complex features (like new Social dynamics) without bloating the core Engine.