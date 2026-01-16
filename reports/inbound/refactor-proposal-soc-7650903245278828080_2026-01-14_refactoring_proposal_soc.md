# Refactoring Proposal: Separation of Concerns (SoC) & God Class Decomposition
**Date:** 2026-01-14
**Author:** Jules (AI Architect)

## 1. Executive Summary

The current simulation codebase has evolved significantly, leading to the emergence of "God Classes"—classes that know too much and do too much. This violates the Single Responsibility Principle (SRP) and Separation of Concerns (SoC), making the system difficult to test, extend, and debug.

This report identifies the primary offenders and proposes a structural refactoring plan to decompose these classes into cohesive, loosely coupled components.

## 2. Identified God Classes

The following classes have been identified as high-priority targets for refactoring based on line count, complexity, and responsibility overload:

| Class | File Path | Line Count | Primary Violation |
|-------|-----------|------------|-------------------|
| `Simulation` | `simulation/engine.py` | ~1,270 | Handles orchestration, state management, market clearing, data logging, and sub-system initialization. |
| `Household` | `simulation/core_agents.py` | ~1,100 | Mixes biological state, economic decision-making, social networking, and political logic. |
| `Firm` | `simulation/firms.py` | ~850 | Mixes production physics, financial accounting, HR management, and strategic AI logic. |
| `Government` | `simulation/agents/government.py` | ~540 | Mixes policy formulation (Brain) with bureaucratic execution (Body) and political mechanics. |

---

## 3. Detailed Analysis & Proposals

### 3.1. Class: `Simulation` (The Engine)

**Current Responsibilities:**
- **Agent Lifecycle:** creation, death, and list management.
- **Time Management:** `run_tick` loop control.
- **Market Orchestration:** initializing and clearing markets.
- **Data Collection:** tracking metrics via `EconomicIndicatorTracker`.
- **Sub-system Management:** managing 10+ helper systems (M&A, Demographics, Housing, etc.).
- **Transaction Processing:** handling trade logistics.

**Problem:**
The `Simulation` class is a "Mediator" that has become a "Manager of Everything". It requires a modification whenever a new subsystem is added.

**Refactoring Proposal: The "World Container" Pattern**

1.  **Extract `AgentManager`**:
    *   Responsibility: Holds lists of agents (`households`, `firms`), handles ID generation, agent lookup, and lifecycle events (spawn/kill).
    *   *Benefit:* `Simulation` no longer needs to filter lists or manage IDs.

2.  **Extract `MarketManager`**:
    *   Responsibility: Holds `markets` dict, handles clearing orders, and triggering matching.
    *   *Benefit:* Encapsulates market initialization and execution.

3.  **Extract `TurnOrchestrator` (The Loop)**:
    *   Responsibility: Defines the order of operations for a tick.
    *   *Benefit:* Decouples the "What happens" from the "State of the world".

**Proposed Structure:**
```python
class Simulation:
    def __init__(self, ...):
        self.state = WorldState(agents, markets) # Data Container
        self.systems = SystemManager(self.state) # Logic Containers
        self.logger = SimulationLogger()

    def run_tick(self):
        self.systems.run_all(self.time)
```

### 3.2. Class: `Household` (The Agent)

**Current Responsibilities:**
- **Biology:** Aging, Hunger, Needs (`update_needs`, `consume`).
- **Economics:** Working, Buying, Budgeting (`make_decision`).
- **Sociology:** Marriage, Vanity, Politics (`update_political_opinion`).
- **Cognition:** AI Learning, Memory (`decision_engine`).

**Problem:**
A change in "Hunger logic" requires editing the same file as "Stock Investment logic". This makes unit testing specific behaviors (like simple budgeting) impossible without mocking the entire biological state.

**Refactoring Proposal: Component-Entity Logic**

1.  **Extract `BiologicalState`**:
    *   Attributes: `age`, `gender`, `needs`, `survival_thresholds`.
    *   Methods: `aging()`, `update_hunger()`.

2.  **Extract `EconomicState`**:
    *   Attributes: `assets`, `inventory`, `jobs`, `portfolio`.
    *   Methods: `transact()`, `calculate_net_worth()`.

3.  **Extract `SocialProfile`**:
    *   Attributes: `spouse_id`, `children`, `political_alignment`, `social_rank`.

**Refactoring Strategy:**
Use a Composition pattern where `Household` becomes a wrapper:
```python
class Household(BaseAgent):
    def __init__(self, ...):
        self.bio = BiologicalComponent(...)
        self.econ = EconomicComponent(...)
        self.social = SocialComponent(...)
        self.brain = DecisionEngine(...)
```

### 3.3. Class: `Firm` (The Producer)

**Current Responsibilities:**
- **Production:** Cobb-Douglas inputs/outputs.
- **Finance:** Accounting, Tax, Dividends, Valuation.
- **HR:** Hiring/Firing logic (partially delegated but leaky).
- **Brand:** Marketing spend and awareness.

**Problem:**
The `produce` method is intertwined with inventory management and technology updates. Financial logic is scattered across `update_needs` and `distribute_profit`.

**Refactoring Proposal:**

1.  **Enhance `FinanceDepartment`**:
    *   Move *all* money handling here. `assets` should ideally be managed by this component, or strictly controlled.
    *   Move `calculate_valuation`, `distribute_profit`, `issue_shares` entirely to this component.

2.  **Extract `ProductionFacility`**:
    *   Responsibility: Holds `capital_stock`, `automation_level`, `inventory`.
    *   Methods: `produce(labor_input)`, `invest_capex()`.

3.  **Strict Facade Pattern**:
    *   The `Firm` class should only delegate. It should not contain calculation logic (e.g., `_calculate_invisible_hand_price` should be in a `MarketAnalyst` component).

### 3.4. Class: `Government` (The Leviathan)

**Current Responsibilities:**
- **Policy Maker:** Taylor Rule, Fiscal decisions.
- **Tax Agency:** Calculating/Collecting taxes.
- **Welfare Office:** Distributing subsidies.
- **Political Entity:** Winning elections.

**Problem:**
The "Brain" (Deciding tax rate) is mixed with the "Body" (Collecting money).

**Refactoring Proposal:**

1.  **Separate `FiscalAuthority` (Body)**:
    *   Purely mechanical. "Collect X% from Agent Y", "Pay Z to Agent A".
    *   Stateless regarding policy (just follows orders).

2.  **Separate `PolicyBrain` (Mind)**:
    *   Purely analytical. Reads sensory data, outputs `GovernmentDirective` (e.g., "Set Tax Rate to 0.15").
    *   Already started with `policy_engine`, but integration needs cleanup.

3.  **Separate `PoliticalSystem` (Game)**:
    *   Handles `approval_rating`, `elections`, `regime_change`.

---

## 4. Implementation Roadmap

### Phase A: Preparation (Low Risk)
1.  Create `AgentManager` and `MarketManager` classes but keep them inside `engine.py` temporarily to test logic.
2.  Move all static calculation methods (e.g., `calculate_valuation`, `calculate_tax`) to utility helpers or existing components.

### Phase B: Extraction (Medium Risk)
3.  **Firm Refactor**: Fully migrate financial logic to `FinanceDepartment`. Remove direct asset manipulation from `Firm` class where possible.
4.  **Household Refactor**: Group attributes into Data Classes (`BioData`, `EconData`) inside the Household to visualize the split.

### Phase C: Structural Severance (High Risk)
5.  **Simulation Refactor**: Replace `self.households` list with `self.agent_manager.households`.
6.  **Household Refactor**: Replace `self.needs` with `self.bio.needs`. This will break *many* references, requiring a comprehensive `grep` and replace across the codebase.

## 5. Conclusion

Refactoring these God Classes is essential for the "Separation of Concerns" principle. By isolating Biology, Economics, and Physics, we can iterate on the AI (Economics) without breaking the World (Physics/Biology).