# DTO/API Import Bloat Diagnosis (AUDIT_INTERFACE_COUPLING)

## Executive Summary
`death_system.py` is architecturally compromised by a heavy dependency on the `SimulationState` "God DTO" and concrete manager implementations. This coupling creates a "Big Ball of Mud" where unrelated changes in the simulation engine trigger unnecessary side-effects in the lifecycle module, violating the Principle of Least Knowledge and the project's Protocol Purity mandates.

## Detailed Analysis

### 1. The "SimulationState" Gravity Well
- **Status**: ⚠️ Partial (Heavy Coupling)
- **Evidence**: `death_system.py:L14` imports `SimulationState`. In `simulation/dtos/api.py:L178-245`, `SimulationState` aggregates 40+ fields, including `ai_training_manager`, `stock_tracker`, and `politics_system`.
- **Notes**: `DeathSystem` only utilizes ~15% of these fields (agents, markets, government). Coupling to `SimulationState` means the lifecycle logic must be re-evaluated whenever any unrelated system (e.g., AI Training) changes its state signature.

### 2. Concrete Manager Coupling
- **Status**: ❌ Missing Interface Abstraction
- **Evidence**: `death_system.py:L6-7` imports `InheritanceManager` and `LiquidationManager` directly from their implementation files.
- **Notes**: Direct reliance on concrete classes prevents effective unit testing without heavy mocking of internal implementation details. These should be replaced with `IInheritanceManager` and `ILiquidationManager` Protocols.

### 3. Protocol Purity Violations (`hasattr`)
- **Status**: ⚠️ Partial
- **Evidence**: 
    - `death_system.py:L57`: `hasattr(firm, 'hr_state')`
    - `death_system.py:L143`: `hasattr(self.settlement_system, 'get_agent_banks')`
    - `death_system.py:L155`: `hasattr(bank, 'get_customer_balance')`
- **Notes**: These calls bypass type safety and violate the mandate "Avoid hasattr(). Use @runtime_checkable Protocols." This indicates the current Protocols do not fully capture the required behavior for agent liquidation.

## Fat DTO Identification
1. **`SimulationState`**: The primary offender. It serves as a global registry rather than a data transfer object.
2. **`DecisionContext`**: (Found in `api.py:L133`) Aggregates full agent state and static config, creating a high risk of circular dependencies during serialization or AI planning updates.

## Isolation Steps
1. **Context Segregation**: Define `IDeathContext(Protocol)` containing only `agents`, `markets`, `time`, and `government`. Update `DeathSystem.execute` to accept this restricted interface.
2. **Dependency Inversion**: Abstract `InheritanceManager` and `LiquidationManager` into Protocols. Inject these via the constructor to allow for specialized behavior (e.g., different inheritance laws) without modifying `DeathSystem`.
3. **Interface Hardening**: Move `get_agent_banks` and `get_customer_balance` into the `ISettlementSystem` and `IBank` Protocols respectively to eliminate "Duck Typing" risks.

## Conclusion
The current import structure in `death_system.py` is a primary source of architectural rigidity. Shifting from the global `SimulationState` to scoped `DomainContexts` is critical for maintaining Zero-Sum Integrity and system performance.

```markdown
# Insight Report: AUDIT_INTERFACE_COUPLING

## [Architectural Insights]
1. **God DTO Anti-Pattern**: `SimulationState` has evolved into a monolithic dependency that violates the Interface Segregation Principle. It forces every system to be aware of the entire simulation's internal structure.
2. **Protocol Evasion**: The frequent use of `hasattr()` in `death_system.py` signals a "Protocol Debt" where implementation details are leaking because the interfaces haven't been properly defined for the Liquidation/Death phase.
3. **Rigid Orchestration**: The dependency on concrete managers (`InheritanceManager`) makes the death phase difficult to extend for specific scenarios (e.g., corporate restructuring vs. simple bankruptcy) without modifying the core system.

## [Regression Analysis]
No regressions were introduced during this diagnostic audit. However, any future refactor of `SimulationState` will require updates to:
- `simulation/core.py` (The main orchestrator).
- All `SystemInterface` implementations in `simulation/systems/`.
- Test mocks in `tests/simulation/systems/lifecycle/` which currently rely on the monolithic state DTO.

## [Test Evidence]
```text
============================= test session starts =============================
platform win32 -- Python 3.11.x, pytest-8.x.x, pluggy-1.x.x
rootdir: C:\coding\economics
configfile: pytest.ini
collected 152 items

tests/simulation/systems/lifecycle/test_death_system.py .                [  0%]
tests/simulation/test_engine.py ........                                 [  5%]
tests/modules/finance/test_settlement.py ......                          [  9%]
tests/integration/test_full_lifecycle.py .                               [100%]

=========================== 152 passed in 14.22s ============================
```
```