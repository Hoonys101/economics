# AUDIT_REPORT_STRUCTURAL: Structural Integrity Audit (v2.0)

## 1. Executive Summary
This audit evaluated the codebase against the `AUDIT_SPEC_STRUCTURAL.md` ruleset, focusing on architectural adherence to the 'DTO-based Decoupling' and 'Component SoC' principles. Several high-impact technical debts were found:
1. The presence of God Classes exceeding the 800-line limit.
2. Leaky Abstractions where internal agent data types (`Dict[str, Any]`) bypass Purity Gates.
3. Centralized state mutation logic nested inside large entity classes (`Firm` & `Household`) instead of domain-specific components.

## 2. God Class Analysis (Classes > 800 lines)

The scan identified three primary God Classes that manage multiple disparate domain responsibilities:

| File | Class | LOC (Approx) | Discovered Domain Mixing |
|---|---|---|---|
| `simulation/firms.py` | `Firm` | ~1765 | Production, Marketing, Finance, HR (State mutation logic integrated within `make_decision` rather than engine boundaries). |
| `simulation/core_agents.py` | `Household` | ~1181 | AI state preparation, Needs management, Budgeting, Labor supply generation. |
| `simulation/systems/settlement_system.py` | `SettlementSystem` | ~966 | Atomic transfers, Multi-party settlements, Macro-financial M2 calculations, Market fee processing. |

**Recommendation:**
- `Firm` and `Household` must become lightweight orchestrators. State mutations (e.g., `self.sales_state.last_prices.update()`) should be delegated to domain-specific services or components.
- `SettlementSystem` should be decomposed into dedicated strategy or ledger handler classes.

## 3. Leaky Abstraction Analysis (DecisionContext & make_decision)

### Positive Adherence (DTO Pattern)
- `DecisionContext` in both `Firm` and `Household` correctly instantiates snapshot DTOs (`self.get_snapshot_dto()`, `self.create_state_dto()`) before passing them to the decision engines.

### Structural Leaks (Raw Agent Leaks into Decision Engines)
- **HouseholdAI Data Coupling**:
  - `HouseholdAI` methods (`decide_action_vector`, `decide_reproduction`, `decide_time_allocation`) accept `agent_data: Dict[str, Any]` and `market_data: Dict[str, Any]`.
  - The decision logic accesses fields directly using dictionary gets (e.g., `agent_data.get("market_insight", 0.5)`). This bypasses the structural guarantees of `HouseholdStateDTO`, creating a hidden dependency on the raw data structure of the household agent, leading to "Mock Fantasy" vulnerabilities.
- **Firm Execution Coupling**:
  - `Firm.make_decision()` orchestrates the lifecycle of decision execution manually. Instead of an engine emitting a command/intent that the Firm blindly routes, the Firm itself unpacks the intent and modifies its internal components directly:
    ```python
    for agent_id, wage in hr_intent.wage_updates.items():
        if int(agent_id) in self.hr_state.employee_wages:
            self.hr_state.employee_wages[int(agent_id)] = wage
    ```
    This directly violates Component SoC. The HR engine/component should own this state transition.

## 4. Sequence & Component Independence

### Purity Gate Bypassing
- Utilities and decision engines occasionally rely on raw dictionary keys instead of typed DTO attributes. This prevents proper type checking and creates integration hazards when agent structures change.
- `HouseholdAI._apply_perceptual_filters` and `_get_common_state` are tightly coupled to the internal dictionary representation of the Household, representing a raw agent leak into the AI decision engine.

## 5. Suggested Refactoring Roadmap
1. **DTO Enforcement in AI Engines:** Refactor `HouseholdAI` to strictly consume `HouseholdStateDTO` (or domain-specific slices of it) instead of `Dict[str, Any]`. Replace all `.get("key")` calls with typed property accesses.
2. **Intent-Driven State Mutation:** Refactor `Firm.make_decision` to use a Command/Intent pattern where the output of an engine is passed to a bounded Component (e.g., `HRComponent`) that handles the state mutation natively, removing the logic from the God Class.
3. **Decompose SettlementSystem:** Isolate M2 tracking and multi-party settlement logic into discrete handler components to bring the LOC below 800 and improve testability.
