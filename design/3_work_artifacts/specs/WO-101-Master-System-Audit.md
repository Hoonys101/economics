# Master System Audit Plan:

## Objective
Verify the consistency between the intended architecture (described in design docs) and the actual implementation (code). Identify architectural drift, hidden coupling, and logic bottlenecks causing simulation failure.

## Auditor Perspectives

### Auditor 1: Core Loop & DTO Integrity
- **Target**: `simulation/core_agents.py`, `simulation/firms.py`, `simulation/dtos/api.py`.
- **Focus**: Check if `DecisionContext` and `StateDTOs` have become bloated or redundant. Verify the separation between "Agent State" and "Engine Logic".

### Auditor 2: Economic Flow (The "Money Trail")
- **Target**: `simulation/economy_manager.py`, `simulation/markets/`, `simulation/models.py`.
- **Focus**: Audit the money supply. Does `record_revenue/expense` always match asset transfers? Are there any hardcoded market IDs causing silent failures?

### Auditor 3: Firm SoC Refactor Consistency
- **Target**: `simulation/components/` (Finance, Production, Sales, HR), `simulation/firms.py`.
- **Focus**: Ensure internal departments don't have conflicting states. Why are firms bankrupting despite having inventory? Check maintenance fee logic.

### Auditor 4: Household Facade & Utility Pipeline
- **Target**: `simulation/components/econ_component.py`, `simulation/decisions/rule_based_household_engine.py`.
- **Focus**: Trace the `survival` need to `Bid` generation. Is the `Price Perception` logic consistent with the market data provided?

### Auditor 5: Macro Scheduling & Global Systems
- **Target**: `main.py`, `simulation/systems/`, `config.py`.
- **Focus**: Sequence of Operations within one tick (Tick Sequencing). Do firms act before or after households? How do `TechnologyManager` and `Bank` influence the loop?
