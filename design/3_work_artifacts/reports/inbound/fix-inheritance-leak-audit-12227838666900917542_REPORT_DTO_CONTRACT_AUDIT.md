# Report: DTO Contract and Communication Audit (TD-118, TD-151)

## Executive Summary
The audit finds that the `HouseholdStateDTO.inventory` field is correctly and consistently implemented as a dictionary, showing no `List` vs. `Dict` discrepancy in the provided code. However, the system is only partially migrated to a DTO-only communication architecture, with significant violations in agent-level method signatures that pass direct object references instead of static data contracts.

## Detailed Analysis

### 1. `HouseholdStateDTO.inventory` Discrepancy (TD-118)
- **Status**: ✅ Implemented / No Discrepancy Found
- **Evidence**:
    - The `Household` internal state for inventory is initialized as a dictionary: `inventory={}` (`simulation/core_agents.py:L142`).
    - The public property for inventory is explicitly type-hinted as a dictionary: `@property def inventory(self) -> Dict[str, float]` (`simulation/core_agents.py:L320-L322`).
    - The `create_state_dto` method correctly populates the `inventory` field by making a copy of the internal dictionary: `inventory=self._econ_state.inventory.copy()` (`simulation/core_agents.py:L700`).
- **Notes**: The premise of an inventory type discrepancy between `List` and `Dict` is not supported by the current codebase. The implementation is consistent across the agent's internal state and its DTO representation.

### 2. DTO-Only Communication (TD-151)
- **Status**: ⚠️ Partial
- **Evidence (Violation)**: The `Household.make_decision` method signature directly accepts complex object references, which violates the architectural principle of communicating via static DTOs only.
    - **File**: `simulation/core_agents.py:L825-L838`
    - **Code**:
      ```python
      def make_decision(
          self,
          markets: Dict[str, IMarket],
          # ...
          government: Optional[Any] = None,
          # ...
      )
      ```
    - **Analysis**: Passing `markets` (a dictionary of `IMarket` interface objects) and `government` (an agent object) is a direct breach of the data contract rules specified in `design/1_governance/architecture/ARCH_SYSTEM_DESIGN.md`, which mandates communication via DTOs to ensure loose coupling.

- **Evidence (Partial Adherence)**: Within `make_decision`, the agent correctly assembles a `DecisionContext` DTO to pass to its internal decision engine. This shows that the pattern is understood but not universally applied.
    - **File**: `simulation/core_agents.py:L848-L856`

- **Evidence (Good Practice)**: The main `Simulation` engine facade demonstrates correct adherence to the DTO-first principle, exposing system and market states through dedicated DTOs.
    - **File**: `simulation/engine.py`
    - **Code**: `get_market_snapshot()` returns a `MarketSnapshotDTO` (`L127`), and `get_system_state()` returns a `SystemStateDTO` (`L142`).

## Risk Assessment
The primary risk stems from the violation of the DTO-only communication pattern. Passing direct object references (`markets`, `government`) into agent methods creates high coupling between the agents and the core simulation infrastructure. This makes the system:
- **Brittle**: Internal changes to `Market` or `Government` implementations are more likely to break agent-level logic.
- **Difficult to Test**: Agent decision logic cannot be tested in isolation without mocking complex, stateful infrastructure objects.
- **Harder to Debug & Scale**: Data flow is not explicit, making it difficult to trace how and where state is being modified. This contradicts the principle of "관찰 가능성" (observability) from the design document.

## Conclusion
While the specific issue with the `inventory` data type (TD-118) appears to be resolved or was based on outdated information, the system-wide migration to DTO-only communication (TD-151) is incomplete. Critical agent interaction points still rely on passing live object references, undermining the project's stated architectural goals. To align with `ARCH_SYSTEM_DESIGN.md`, the `Household.make_decision` signature and similar methods must be refactored to accept only DTOs containing the necessary data from markets and other systems.